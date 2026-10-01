"""Runtime verification is unavailable until an isolated executor exists.

A configuration flag cannot itself establish network, process, filesystem,
identity, and resource isolation. Keep this gate fail-closed.
"""


def verification_runtime_available() -> bool:
    return False
