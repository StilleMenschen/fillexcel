import logging
import pathlib
import time
from logging.handlers import TimedRotatingFileHandler

import xlwings as xw
from celery import Celery

app = Celery('fills',
             broker='amqp://invoice:40Z9y5RqCNecG6Fx@gz.tystnad.tech:32765//',
             backend='redis://default:ZI6vLhsHdKCjeiyw@gz.tystnad.tech:46379/1')


def init_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    log_path = pathlib.Path(__file__).parent.parent / 'var' / 'logs'
    log_format = logging.Formatter(fmt='%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler = logging.FileHandler(filename=str(log_path / 'example.log'))
    file_handler.setFormatter(log_format)

    rotating_file_handler = TimedRotatingFileHandler(filename=str(log_path / 'rotating-example.log'), when='midnight')
    rotating_file_handler.setFormatter(log_format)

    logger.addHandler(file_handler)
    logger.addHandler(rotating_file_handler)

    return logger


log = init_logger()


# celery -A fills.tasks worker -l INFO -c 2 -P eventlet

@app.task
def write_to_excel(data_for_fill: dict):
    t0 = time.perf_counter()
    start_line = data_for_fill['startLine']
    excel_data: dict = data_for_fill['data']
    excel_app = xw.App(visible=False)
    book = excel_app.books.active
    sheet = book.sheets.active
    for column, data_list in excel_data.items():
        range_len = len(data_list)
        sheet.range(f'{column}{start_line}').value = tuple((v,) for v in data_list)
        sheet.range(f'{column}{start_line}:{column}{start_line + range_len}').number_format = '@'
    filename = f"{time.time_ns()}-{data_for_fill['filename']}"
    p = pathlib.Path(__file__).parent / filename
    book.save(path=p)
    book.close()
    excel_app.quit()
    log.info(f'elapsed time {time.perf_counter() - t0}')
    return filename
