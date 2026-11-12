#!/bin/bash
#
# Tests tree-already-tested.sh with a stand-in GitLab API: test-tree-already-tested.sh
#
# Checks that a develop merge commit whose tree a pull request pipeline already passed:
# - is reused only when that pipeline was a full pass: its child pipeline ran every job of FULL_JOBS and passed it;
# - is not reused after a partial pass (a branch pipeline that skipped the valgrind or Python suite jobs), after a
#   pipeline whose child pipeline failed or is missing, or when only this pipeline itself passed;
# - picks a later full pass of the same commit after a partial one;
# - fails open (reuses nothing) when the pipeline list, the trigger jobs or the jobs cannot be read;
# and that every job in FULL_JOBS is a job of .gitlab/ci/module-xml.yml. Needs git, python3 and bash; takes about 4 s
# in the CI images.
# Exits nonzero on the first failed check.
#
# Copyright 2026 Qore Technologies, s.r.o.

set -e

here=$(cd "$(dirname "$0")" && pwd)
script=${here}/tree-already-tested.sh
yml=${here}/../../.gitlab/ci/module-xml.yml
dir=$(mktemp -d)
trap 'rm -rf "${dir}"' EXIT

fail() {
    echo "test-tree-already-tested.sh: FAILED: $*" >&2
    if [ -f "${dir}/out.txt" ]; then
        sed 's/^/    | /' "${dir}/out.txt" >&2
    fi
    exit 1
}

# every job the script requires exists in the child pipeline
full_jobs=$(sed -n 's/^FULL_JOBS=\${FULL_JOBS:-"\(.*\)"}$/\1/p' "${script}")
[ -n "${full_jobs}" ] || fail "FULL_JOBS not found in tree-already-tested.sh"
for job in ${full_jobs}; do
    grep -q "^${job}:\$" "${yml}" || fail "FULL_JOBS names ${job}, which is not a job of module-xml.yml"
done

# a repository with a pull request branch merged into develop without changes: the merge has the branch's tree
repo=${dir}/repo
git init -q -b develop "${repo}"
cd "${repo}"
git -c user.email=t@t -c user.name=t commit -q --allow-empty -m base
git checkout -q -b pr
echo change > file
git add file
git -c user.email=t@t -c user.name=t commit -q -m change
pr=$(git rev-parse HEAD)
git checkout -q develop
git -c user.email=t@t -c user.name=t merge -q --no-ff -m merge pr
merge=$(git rev-parse HEAD)

# the stand-in API: curl prints ${dir}/api/<path with "/" and "?" replaced> or fails as curl -f does
mkdir -p "${dir}/bin" "${dir}/api"
cat > "${dir}/bin/curl" <<'EOF'
#!/bin/sh
for arg; do url=$arg; done
path=${url#*/projects/93/}
file=$(printf '%s' "${path}" | tr '/?&=' '____')
if [ -f "${API_DIR}/${file}" ]; then
    cat "${API_DIR}/${file}"
    exit 0
fi
exit 22
EOF
chmod +x "${dir}/bin/curl"

# api PATH CONTENT: the response to a path
api() {
    printf '%s' "$2" > "${dir}/api/$(printf '%s' "$1" | tr '/?&=' '____')"
}

# pipelines COMMIT ID...: the successful pipelines of a commit
pipelines() {
    commit=$1
    shift
    list=
    for id; do
        list="${list}${list:+,}{\"id\":${id},\"sha\":\"${commit}\",\"status\":\"success\",\"user\":{\"name\":\"x\"}}"
    done
    api "pipelines?sha=${commit}&status=success&per_page=20" "[${list}]"
}

# child PARENT CHILD STATUS JOB...: the trigger job of a pipeline and the jobs of its child pipeline, all passed
child() {
    parent=$1
    id=$2
    api "pipelines/${parent}/bridges" "[{\"name\":\"module-xml\",\"status\":\"$3\",\"user\":{\"name\":\"x\"},\"downstream_pipeline\":{\"id\":${id}}}]"
    shift 3
    jobs=
    for job; do
        jobs="${jobs}${jobs:+,}{\"name\":\"${job}\",\"status\":\"success\",\"user\":{\"name\":\"someone\"},\"commit\":{\"author_name\":\"x\"}}"
    done
    api "pipelines/${id}/jobs?per_page=100" "[${jobs}]"
}

# run: runs the script as the develop pipeline 900 of the merge commit
run() {
    rm -f tree-tested.env
    PATH=${dir}/bin:${PATH} API_DIR=${dir}/api CI_API_V4_URL=https://gitlab.example/api/v4 CI_PROJECT_ID=93 \
        CI_PIPELINE_ID=900 CI_JOB_TOKEN=token sh "${script}" > "${dir}/out.txt" 2>&1 || fail "the script failed"
    [ -f tree-tested.env ] || fail "no tree-tested.env"
}

# expect_reused PIPELINE COMMIT | expect_none
expect_reused() {
    grep -qx "QORE_TREE_TESTED_IN=$1" tree-tested.env || fail "expected pipeline $1 to be reused"
    grep -qx "QORE_TREE_TESTED_SHA=$2" tree-tested.env || fail "expected commit $2"
}
expect_none() {
    if grep -q QORE_TREE_TESTED_IN tree-tested.env; then
        fail "expected no pipeline to be reused: $(cat tree-tested.env)"
    fi
    grep -qx QORE_TREE_TESTED_CHECKED=1 tree-tested.env || fail "no QORE_TREE_TESTED_CHECKED"
}

reset() {
    rm -f "${dir}"/api/*
    pipelines "${merge}" 900
}

# a full pass of the pull request head is reused
reset
pipelines "${pr}" 800
child 800 801 success ${full_jobs} qtest-passed "python-ubuntu 1/2" "python-ubuntu 2/2"
run
expect_reused 800 "${pr}"

# a partial pass, without the Python suite or valgrind jobs, is not
for missing in python-verify-ubuntu python-verify-alpine test-valgrind; do
    reset
    pipelines "${pr}" 800
    child 800 801 success $(for job in ${full_jobs}; do [ "${job}" = "${missing}" ] || echo "${job}"; done) qtest-passed
    run
    expect_none
    grep -q "did not run and pass ${missing}" "${dir}/out.txt" || fail "the missing job ${missing} is not named"
done

# a job name only containing a required one does not count
reset
pipelines "${pr}" 800
child 800 801 success $(for job in ${full_jobs}; do [ "${job}" = test-valgrind ] || echo "${job}"; done) \
    "x test-valgrind" "test-valgrind 1/2"
run
expect_none

# a later full pass of the same commit is found after a partial one
reset
pipelines "${pr}" 810 800
child 810 811 success test-ubuntu
child 800 801 success ${full_jobs}
run
expect_reused 800 "${pr}"

# a child pipeline that did not pass, or a pipeline without one, is not reused
reset
pipelines "${pr}" 800
child 800 801 failed ${full_jobs}
run
expect_none
reset
pipelines "${pr}" 800
api "pipelines/800/bridges" "[]"
run
expect_none

# only this pipeline passed (the merge commit itself): nothing to reuse
reset
run
expect_none

# the merge commit's own earlier full pass (a pipeline on another ref) is reused
reset
pipelines "${merge}" 900 850
child 850 851 success ${full_jobs}
run
expect_reused 850 "${merge}"

# fail open: the pipeline list, the trigger jobs or the jobs cannot be read
rm -f "${dir}"/api/*
run
expect_none
grep -q "cannot read the pipelines" "${dir}/out.txt" || fail "an unreadable pipeline list is not reported"
reset
pipelines "${pr}" 800
run
expect_none
grep -q "cannot read the jobs of pipeline 800" "${dir}/out.txt" || fail "unreadable trigger jobs are not reported"
reset
pipelines "${pr}" 800
child 800 801 success ${full_jobs}
rm -f "${dir}/api/pipelines_801_jobs_per_page_100"
run
expect_none
grep -q "cannot read the jobs of pipeline 800" "${dir}/out.txt" || fail "unreadable jobs are not reported"
# malformed JSON
reset
api "pipelines?sha=${merge}&status=success&per_page=20" "not json"
run
expect_none

echo "test-tree-already-tested.sh: all checks passed"
