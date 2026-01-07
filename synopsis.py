import k3wsjobd
from k3wsjobd import logging


def run():
    k3wsjobd.run(ip="127.0.0.1", port=33445)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler("wsjobd.log")
    formatter = logging.Formatter("[%(asctime)s, %(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    run()
