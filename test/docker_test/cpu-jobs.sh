#!/bin/sh
#
# Prints the number of CPUs that this container may use: cpu-jobs.sh
#
# A Kubernetes CPU limit is a CFS quota, which nproc does not see: in a CI job pod limited to 4 CPUs nproc reports all
# the node's CPUs (32), and sizing parallel work by it would overload the job. The quota of the container's cgroup
# (cgroup v2 cpu.max, or cgroup v1 cpu.cfs_quota_us and cpu.cfs_period_us), rounded up, is printed when there is one,
# and otherwise nproc.
#
# Copyright 2026 Qore Technologies, s.r.o.

quota=
period=
if [ -r /sys/fs/cgroup/cpu.max ]; then
    read -r quota period < /sys/fs/cgroup/cpu.max
elif [ -r /sys/fs/cgroup/cpu/cpu.cfs_quota_us ] && [ -r /sys/fs/cgroup/cpu/cpu.cfs_period_us ]; then
    read -r quota < /sys/fs/cgroup/cpu/cpu.cfs_quota_us
    read -r period < /sys/fs/cgroup/cpu/cpu.cfs_period_us
fi
case "${quota}:${period}" in
    *[!0-9:]*|:*|*:) nproc ;;
    *)
        if [ "${quota}" -gt 0 ] && [ "${period}" -gt 0 ]; then
            echo $(( (quota + period - 1) / period ))
        else
            nproc
        fi
        ;;
esac
