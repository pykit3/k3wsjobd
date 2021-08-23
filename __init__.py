"""
This module is a gevent based websocket server. When the server receives a job description from a client,
it runs that job asynchronously in a thread, and reports the progress back to the client periodically.

"""

__version__ = "0.1.0"
__name__ = "k3wsjobd"

from .wsjobd import (
    JobdWebSocketApplication,
    Job,
    run,

    SystemOverloadError,
    JobError,
    InvalidMessageError,
    InvalidProgressError,
    LoadingError,
    JobNotInSessionError
)

__all__ = [
    'JobdWebSocketApplication',
    'Job',
    'run',

    "SystemOverloadError",
    "JobError",
    "InvalidMessageError",
    "InvalidProgressError",
    "LoadingError",
    "JobNotInSessionError"
]
