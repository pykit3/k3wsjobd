# DO NOT EDIT!!! built with `python _building/build_setup.py`
import setuptools
setuptools.setup(
    name="k3wsjobd",
    packages=["k3wsjobd"],
    version="0.1.0",
    license='MIT',
    description='This module is a gevent based websocket server. When the server receives a job description from a client, it runs that job asynchronously in a thread, and reports the progress back to the client periodically.',
    long_description='# k3wsjobd\n\n[![Action-CI](https://github.com/pykit3/k3wsjobd/actions/workflows/python-package.yml/badge.svg)](https://github.com/pykit3/k3wsjobd/actions/workflows/python-package.yml)\n[![Build Status](https://travis-ci.com/pykit3/k3wsjobd.svg?branch=master)](https://travis-ci.com/pykit3/k3wsjobd)\n[![Documentation Status](https://readthedocs.org/projects/k3wsjobd/badge/?version=stable)](https://k3wsjobd.readthedocs.io/en/stable/?badge=stable)\n[![Package](https://img.shields.io/pypi/pyversions/k3wsjobd)](https://pypi.org/project/k3wsjobd)\n\nThis module is a gevent based websocket server. When the server receives a job description from a client, it runs that job asynchronously in a thread, and reports the progress back to the client periodically.\n\nk3wsjobd is a component of [pykit3] project: a python3 toolkit set.\n\n\nThis module is a gevent based websocket server. When the server receives a job description from a client,\nit runs that job asynchronously in a thread, and reports the progress back to the client periodically.\n\n\n\n\n# Install\n\n```\npip install k3wsjobd\n```\n\n# Synopsis\n\n```python\n\nfrom geventwebsocket import Resource, WebSocketServer\nimport k3wsjobd\nfrom k3wsjobd import logging\n\n\ndef run():\n    k3wsjobd.run(ip=\'127.0.0.1\', port=33445)\n\n\nif __name__ == "__main__":\n    logger = logging.getLogger()\n    logger.setLevel(logging.INFO)\n\n    file_handler = logging.FileHandler(\'wsjobd.log\')\n    formatter = logging.Formatter(\'[%(asctime)s, %(levelname)s] %(message)s\')\n    file_handler.setFormatter(formatter)\n    logger.addHandler(file_handler)\n    run()\n\n```\n\n#   Author\n\nZhang Yanpo (张炎泼) <drdr.xp@gmail.com>\n\n#   Copyright and License\n\nThe MIT License (MIT)\n\nCopyright (c) 2015 Zhang Yanpo (张炎泼) <drdr.xp@gmail.com>\n\n\n[pykit3]: https://github.com/pykit3',
    long_description_content_type="text/markdown",
    author='Zhang Yanpo',
    author_email='drdr.xp@gmail.com',
    url='https://github.com/pykit3/k3wsjobd',
    keywords=['python', 'thread'],
    python_requires='>=3.0',

    install_requires=['k3ut<0.2,>=0.1.15', 'k3utfjson>=0.1.1,<0.2', 'k3thread<0.2,>=0.1.0', 'k3proc<0.3.0,>=0.2.13', 'k3jobq>=0.1.2,<0.2', 'psutil>=5.8.0', 'gevent-websocket>=0.10.1', 'websocket-client>=1.2.0', 'k3daemonize<0.2,>=0.1.0'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
    ] + ['Programming Language :: Python :: 3'],
)
