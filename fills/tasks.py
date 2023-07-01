import logging
import pathlib
import time
from logging.handlers import TimedRotatingFileHandler

import xlwings as xw
from celery import Celery

app = Celery('fills',
             broker='amqp://invoice:40Z9y5RqCNecG6Fx@gz.tystnad.tech:32765//',
             backend='redis://default:ZI6vLhsHdKCjeiyw@gz.tystnad.tech:46379/1')

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log_path = pathlib.Path(__file__).parent.parent / 'var' / 'logs'
log_format = logging.Formatter(fmt='%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler = logging.FileHandler(filename=str(log_path / 'example.log'))
file_handler.setFormatter(log_format)

rotating_file_handler = TimedRotatingFileHandler(filename=str(log_path / 'rotating-example.log'), when='midnight')
rotating_file_handler.setFormatter(log_format)

log.addHandler(file_handler)
log.addHandler(rotating_file_handler)


# celery -A fills.tasks worker -l INFO -c 2 -P eventlet

@app.task
def write_to_excel(data: dict):
    t0 = time.perf_counter()
    start_line = data['startLine']
    filename = data['filename']
    d: dict = data['data']
    excel_app = xw.App(visible=True)
    book = excel_app.books.active
    sheet = book.sheets.active
    for column, data_list in d.items():
        sheet[f'{column}{start_line}'].value = [(v,) for v in data_list]
        range_len = len(data_list)
        sheet.range(f'{column}{start_line}:{column}{start_line + range_len}').number_format = '@'
    p = pathlib.Path(__file__).parent / filename
    book.save(path=p)
    book.close()
    excel_app.quit()
    log.info(f'elapsed time {time.perf_counter() - t0}')
    return filename
