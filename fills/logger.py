import logging
import pathlib
from logging.handlers import TimedRotatingFileHandler


def init_logger(logger_name, filename):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    log_path = pathlib.Path(__file__).parent.parent / 'var' / 'logs'
    log_format = logging.Formatter(fmt='%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    rotating_file_handler = TimedRotatingFileHandler(filename=str(log_path / filename), when='midnight')
    rotating_file_handler.setFormatter(log_format)

    logger.addHandler(rotating_file_handler)

    return logger
