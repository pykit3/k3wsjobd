# k3wsjobd

[![Action-CI](https://github.com/pykit3/k3wsjobd/actions/workflows/python-package.yml/badge.svg)](https://github.com/pykit3/k3wsjobd/actions/workflows/python-package.yml)
[![Documentation Status](https://readthedocs.org/projects/k3wsjobd/badge/?version=stable)](https://k3wsjobd.readthedocs.io/en/stable/?badge=stable)
[![Package](https://img.shields.io/pypi/pyversions/k3wsjobd)](https://pypi.org/project/k3wsjobd)

Gevent-based WebSocket server for async job processing. Receives job descriptions from clients, runs them asynchronously, and reports progress back periodically.

k3wsjobd is a component of [pykit3](https://github.com/pykit3) project: a python3 toolkit set.

## Installation

```bash
pip install k3wsjobd
```

## Quick Start

```python
import k3wsjobd

# Start WebSocket job server
k3wsjobd.run(ip='127.0.0.1', port=33445)
```

## API Reference

::: k3wsjobd

## License

The MIT License (MIT) - Copyright (c) 2015 Zhang Yanpo (张炎泼)
