#!/usr/bin/env python
# coding: utf-8

import logging

logger = logging.getLogger(__name__)


def run(job):
    data = job.data

    data["result"] = "foo"
