#!/bin/sh
#
# Prints the number of CPUs that this container may use: cpu-jobs.sh
#
# A Kubernetes CPU limit is a CFS quota, which neither BusyBox's nproc nor the CPU affinity mask reflects: in a CI job
# pod limited to 4 CPUs they report all the node's CPUs (32), and sizing parallel work by them would overload the
# job. This prints the smallest CPU quota, rounded up, of the process's cgroup and its ancestors (cgroup v2 cpu.max,
# or cgroup v1 cpu.cfs_quota_us and cpu.cfs_period_us), and nproc when there is none. The cgroup is looked up from
# /proc/self/cgroup: a privileged container (as the CI jobs are) sees the host's cgroup tree, where its own quota is
# in its cgroup's directory, not at /sys/fs/cgroup. The result is at most CPU_JOBS_MAX (default 8), so that a
# container without a quota does not start a job for each of a large node's CPUs.
#
# Copyright 2026 Qore Technologies, s.r.o.

best=

# consider QUOTA PERIOD: keeps the smallest whole number of CPUs
consider() {
    case "$1:$2" in
        *[!0-9:]*|:*|*:) return ;;
    esac
    if [ "$1" -gt 0 ] && [ "$2" -gt 0 ]; then
        n=$(( ($1 + $2 - 1) / $2 ))
        if [ -z "${best}" ] || [ "${n}" -lt "${best}" ]; then
            best=${n}
        fi
    fi
}

# the directories from DIR up to ROOT
walk() {
    dir=$1
    root=$2
    while :; do
        echo "${dir}"
        if [ "${dir}" = "${root}" ] || [ "${dir}" = "/" ]; then
            break
        fi
        dir=$(dirname "${dir}")
    done
}

if [ -r /sys/fs/cgroup/cgroup.controllers ]; then
    # cgroup v2: "0::PATH"
    path=$(sed -n 's/^0:://p' /proc/self/cgroup 2>/dev/null)
    for dir in $(walk "/sys/fs/cgroup${path%/}" /sys/fs/cgroup); do
        if [ -r "${dir}/cpu.max" ]; then
            read -r quota period < "${dir}/cpu.max"
            consider "${quota}" "${period}"
        fi
    done
else
    # cgroup v1: "N:...cpu...:PATH"
    path=$(sed -n 's/^[0-9]*:\([^:]*,\)\{0,1\}cpu\(,[^:]*\)\{0,1\}:\(.*\)$/\3/p' /proc/self/cgroup 2>/dev/null | head -1)
    for base in /sys/fs/cgroup/cpu /sys/fs/cgroup/cpu,cpuacct; do
        [ -d "${base}" ] || continue
        for dir in $(walk "${base}${path%/}" "${base}"); do
            if [ -r "${dir}/cpu.cfs_quota_us" ] && [ -r "${dir}/cpu.cfs_period_us" ]; then
                read -r quota < "${dir}/cpu.cfs_quota_us"
                read -r period < "${dir}/cpu.cfs_period_us"
                consider "${quota}" "${period}"
            fi
        done
        break
    done
fi

if [ -z "${best}" ]; then
    best=$(nproc)
fi
max=${CPU_JOBS_MAX:-8}
if [ "${best}" -gt "${max}" ]; then
    best=${max}
fi
echo "${best}"
