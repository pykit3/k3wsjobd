# k3wsjobd

[![Action-CI](https://github.com/pykit3/k3wsjobd/actions/workflows/python-package.yml/badge.svg)](https://github.com/pykit3/k3wsjobd/actions/workflows/python-package.yml)
[![Build Status](https://travis-ci.com/pykit3/k3wsjobd.svg?branch=master)](https://travis-ci.com/pykit3/k3wsjobd)
[![Documentation Status](https://readthedocs.org/projects/k3wsjobd/badge/?version=stable)](https://k3wsjobd.readthedocs.io/en/stable/?badge=stable)
[![Package](https://img.shields.io/pypi/pyversions/k3wsjobd)](https://pypi.org/project/k3wsjobd)

This module is a gevent based websocket server. When the server receives a job description from a client, it runs that job asynchronously in a thread, and reports the progress back to the client periodically.

k3wsjobd is a component of [pykit3] project: a python3 toolkit set.


This module is a gevent based websocket server. When the server receives a job description from a client,
it runs that job asynchronously in a thread, and reports the progress back to the client periodically.




# Install

```
pip install k3wsjobd
```

# Synopsis

```python

from geventwebsocket import Resource, WebSocketServer
import k3wsjobd
from k3wsjobd import logging


def run():
    k3wsjobd.run(ip='127.0.0.1', port=33445)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler('wsjobd.log')
    formatter = logging.Formatter('[%(asctime)s, %(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    run()

```

#   Author

Zhang Yanpo (张炎泼) <drdr.xp@gmail.com>

#   Copyright and License

The MIT License (MIT)

Copyright (c) 2015 Zhang Yanpo (张炎泼) <drdr.xp@gmail.com>


[pykit3]: https://github.com/pykit3