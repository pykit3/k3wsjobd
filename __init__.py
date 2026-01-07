"""
This module is a gevent based websocket server. When the server receives a job description from a client,
it runs that job asynchronously in a thread, and reports the progress back to the client periodically.

"""

from importlib.metadata import version

__version__ = version("k3wsjobd")

from .wsjobd import (
    JobdWebSocketApplication,
    Job,
    run,
    SystemOverloadError,
    JobError,
    InvalidMessageError,
    InvalidProgressError,
    LoadingError,
    JobNotInSessionError,
)

__all__ = [
    "JobdWebSocketApplication",
    "Job",
    "run",
    "SystemOverloadError",
    "JobError",
    "InvalidMessageError",
    "InvalidProgressError",
    "LoadingError",
    "JobNotInSessionError",
]
