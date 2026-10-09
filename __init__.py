"""
This module is a gevent based websocket server. When the server receives a job description from a client,
it runs that job asynchronously in a thread, and reports the progress back to the client periodically.

"""

from .wsjobd import (
    InvalidMessageError,
    InvalidProgressError,
    Job,
    JobdWebSocketApplication,
    JobError,
    JobNotInSessionError,
    LoadingError,
    SystemOverloadError,
    run,
)

__all__ = [
    "InvalidMessageError",
    "InvalidProgressError",
    "Job",
    "JobError",
    "JobNotInSessionError",
    "JobdWebSocketApplication",
    "LoadingError",
    "SystemOverloadError",
    "run",
]


def __getattr__(name: str) -> str:
    # importlib.metadata takes about 20 ms to import, so it is loaded only
    # when __version__ is read
    if name != "__version__":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib.metadata import version

    return version("k3wsjobd")
