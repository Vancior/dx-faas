import coloredlogs
import logging


def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Prevent logging from propagating to the root logger
        logger.propagate = 0
        console = logging.StreamHandler()
        logger.addHandler(console)
        coloredlogs.install(logger=logger, level='DEBUG',
                            fmt='%(asctime)s %(name)s:%(lineno)d[%(process)d] %(levelname)s %(message)s')
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
        # console.setFormatter(formatter)
    return logger
