#!/usr/bin/env python
# coding: utf-8
import logging
import k3wsjobd

PORT = 33445


def run():
    k3wsjobd.run(ip="127.0.0.1", port=PORT, jobq_thread_count=20)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler("/tmp/wsjobd.log")
    formatter = logging.Formatter("[%(asctime)s, %(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    import k3daemonize

    k3daemonize.daemonize_cli(run, "/tmp/wsjod_server.pid")
