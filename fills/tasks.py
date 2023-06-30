import logging
import pathlib
import time

import xlwings as xw
from celery import Celery

task_app = Celery('fills',
                  broker='amqp://invoice:40Z9y5RqCNecG6Fx@gz.tystnad.tech:32765//',
                  backend='redis://default:ZI6vLhsHdKCjeiyw@gz.tystnad.tech:46379/0')

log = logging.getLogger(__name__)


#  celery -A fills.tasks worker -l INFO -P eventlet

@task_app.task
def excel(data: dict):
    t0 = time.perf_counter()
    start_line = data['startLine']
    filename = data['filename']
    d: dict = data['data']
    app = xw.App(visible=True)
    book = app.books.active
    sheet = book.sheets.active
    for key, value in d.items():
        sheet[f'{key}{start_line}'].value = [[v] for v in value]
    p = pathlib.Path(__file__).parent / filename
    book.save(path=p)
    book.close()
    app.quit()
    log.info(f'elapsed time {time.perf_counter() - t0}')
    return filename
