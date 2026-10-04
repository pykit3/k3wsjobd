import logging

logger = logging.getLogger(__name__)


def run(job):
    data = job.data

    data["foo"] = "80%"
