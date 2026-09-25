"""The environment for the suite's pinned Java oracles and peers.

Copyright (C) 2026 Qore Technologies, s.r.o.

The JVM launchers read options from the environment. A process started with such options prints a notice such
as "Picked up JAVA_TOOL_OPTIONS: ..." on stderr, which the oracles and peers rightly report as an unexpected
diagnostic, and the options themselves, for example ``-Dfile.encoding``, can change their behavior. Java child
processes therefore run without them: their configuration is on their command lines.
"""
import os

# the variables the java and javac launchers read options from
AMBIENT_OPTIONS = ("JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS")


def environment(base=None):
    """Returns a copy of ``base`` (default: the process environment) without the ambient JVM options."""
    source = os.environ if base is None else base
    return {name: value for name, value in source.items() if name not in AMBIENT_OPTIONS}
