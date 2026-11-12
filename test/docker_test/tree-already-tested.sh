#!/bin/sh
# -*- mode: sh -*-
# Copyright (C) 2026 Qore Technologies, s.r.o.
#
# Run by the tree-already-tested job of a develop pipeline: decides whether the commit's tree already passed CI, so
# that the pipeline does not test the same code twice.  Merging a pull request that is up to date with develop makes
# a merge commit whose tree is the pull request head's tree, which the pull request pipeline has just tested.  The
# same job runs in qore's pipelines (examples/test/docker_test/tree-already-tested.sh there).
#
# The candidates are the commit itself (a fast-forward merge, or a pipeline on another ref) and each parent with the
# same tree (the merged pull request head).  Only a full pass counts: a successful pipeline other than this one whose
# child test pipeline (the trigger job "module-xml") ran every job in FULL_JOBS and passed them.  A partial branch
# pipeline, which skips the valgrind or Python suite jobs when the branch changes nothing they exercise (see
# .gitlab/ci/module-xml.yml), therefore does not spare its tree the full develop pipeline.  The first candidate with
# such a pipeline is written to tree-tested.env (a dotenv report):
#   QORE_TREE_TESTED_IN    the ID of the pipeline that passed the tree
#   QORE_TREE_TESTED_SHA   its commit
# and every job of the child test pipeline ends at once with success (tree-tested-skip.sh).
#
# It fails open: when the tree has no fully passed pipeline, or the pipelines cannot be read (no token, an API error),
# tree-tested.env names no pipeline and the whole pipeline runs, as without this job.  The pipelines are read with the
# job token, or with QORE_CI_READ_API_TOKEN (a read_api token, a masked CI variable) where the job token is refused.
# The JSON responses are read with python3.

set -u
# the jobs of a full child pipeline (.gitlab/ci/module-xml.yml); test-tree-already-tested.sh checks that each is a job
# there.  The Python suite's shard jobs have numbered names ("python-ubuntu 1/2"); its verify jobs pass only when
# every shard of their distribution ran completely and passed.  A job renamed or added there without being listed
# here only makes this script find no full pass (fail open).
FULL_JOBS=${FULL_JOBS:-"test-ubuntu test-ubuntu-aot test-alpine test-alpine-aot test-valgrind python-verify-ubuntu python-verify-alpine"}
out=tree-tested.env
# a dotenv report needs one variable even when the tree must be tested
echo "QORE_TREE_TESTED_CHECKED=1" > "$out"

if [ -z "${CI_API_V4_URL:-}" ] || [ -z "${CI_PROJECT_ID:-}" ]; then
    echo "the GitLab API is not known (CI_API_V4_URL, CI_PROJECT_ID): running the full pipeline"
    exit 0
fi

tree=$(git rev-parse 'HEAD^{tree}') || { echo "cannot read the commit's tree: running the full pipeline"; exit 0; }
candidates=$(git rev-parse HEAD)
for parent in $(git rev-list --parents -n 1 HEAD | cut -d' ' -f2-); do
    if [ "$(git rev-parse "${parent}^{tree}" 2>/dev/null)" = "$tree" ]; then
        candidates="$candidates $parent"
    fi
done

# never trace a token
set +x
# api PATH: prints the response of a GET request to the project's API path; a response is printed only when its
# request succeeded, so that the partial output of a failed request is never read
api() {
    url="${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/$1"
    if [ -n "${CI_JOB_TOKEN:-}" ] \
        && body=$(curl -sf --max-time 30 --header "JOB-TOKEN: ${CI_JOB_TOKEN}" "$url"); then
        printf '%s' "$body"
        return 0
    fi
    if [ -n "${QORE_CI_READ_API_TOKEN:-}" ] \
        && body=$(curl -sf --max-time 30 --header "PRIVATE-TOKEN: ${QORE_CI_READ_API_TOKEN}" "$url"); then
        printf '%s' "$body"
        return 0
    fi
    return 1
}

# json SCRIPT: runs a python3 expression on the JSON document on stdin (as "d") and prints its result
json() {
    python3 -c "import json, sys; d = json.load(sys.stdin); print($1)"
}

# full_pass PIPELINE: 0 when the pipeline's child test pipeline ran every job in FULL_JOBS and passed them, 1 when it
# did not, 2 when that cannot be read
full_pass() {
    bridges=$(api "pipelines/$1/bridges") || return 2
    child=$(printf '%s' "$bridges" | json '" ".join(str(b["downstream_pipeline"]["id"]) for b in d
        if b.get("name") == "module-xml" and b.get("status") == "success" and b.get("downstream_pipeline"))') \
        || return 2
    case "$child" in
        ""|*[!0-9]*) return 1 ;;
    esac
    # the latest attempt of each job (retried jobs are left out by default)
    jobs=$(api "pipelines/${child}/jobs?per_page=100") || return 2
    # one name per line: job names may contain spaces ("python-ubuntu 1/2")
    passed=$(printf '%s' "$jobs" | json '"\n".join(sorted(j["name"] for j in d if j.get("status") == "success"))') \
        || return 2
    for job in ${FULL_JOBS}; do
        if ! printf '%s\n' "${passed}" | grep -qxF "${job}"; then
            echo "pipeline $1 (child pipeline ${child}) did not run and pass ${job}: it was not a full pass"
            return 1
        fi
    done
    return 0
}

for commit in $candidates; do
    if ! list=$(api "pipelines?sha=${commit}&status=success&per_page=20"); then
        echo "cannot read the pipelines of $commit: running the full pipeline"
        exit 0
    fi
    if ! ids=$(printf '%s' "$list" | json '" ".join(str(p["id"]) for p in d)'); then
        echo "cannot read the pipelines of $commit: running the full pipeline"
        exit 0
    fi
    for id in $ids; do
        if [ "$id" = "${CI_PIPELINE_ID:-}" ]; then
            continue
        fi
        full_pass "$id"
        case $? in
            0) ;;
            1) continue ;;
            *)
                echo "cannot read the jobs of pipeline $id: running the full pipeline"
                exit 0
                ;;
        esac
        printf 'QORE_TREE_TESTED_IN=%s\nQORE_TREE_TESTED_SHA=%s\n' "$id" "$commit" >> "$out"
        echo "tree $tree already fully passed in pipeline $id on commit $commit: the jobs of this pipeline end at once"
        exit 0
    done
done
echo "tree $tree has no fully passed pipeline: running the full pipeline"
