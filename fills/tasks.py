import os
import pathlib
import tempfile
import time

import xlwings as xw
import psycopg2
from celery import Celery

from .utils import SnowFlake
from .logger import init_logger
from .storage import Storage

app = Celery('fills',
             broker='amqp://invoice:40Z9y5RqCNecG6Fx@gz.tystnad.tech:32765//',
             backend='redis://default:ZI6vLhsHdKCjeiyw@gz.tystnad.tech:46379/1')

log = init_logger(__name__, 'celery-task.log')
storge = Storage()


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
    filename = data_for_fill['filename']
    filename, ext = os.path.splitext(filename)
    filename = f"{filename}-{time.time_ns()}{ext}"
    tempdir = tempfile.TemporaryDirectory()
    tmp_dir = pathlib.Path(tempdir.name)
    save_path = tmp_dir / filename
    book.save(path=save_path)
    book.close()
    excel_app.quit()
    file_id = storge.store_file(save_path)
    tempdir.cleanup()
    save_record(data_for_fill['requirementId'], data_for_fill['username'], file_id, filename)
    log.info(f'elapsed time {time.perf_counter() - t0}')
    return filename


def save_record(requirement_id, username, file_id, filename):
    try:
        connection = psycopg2.connect(user="fillexcel", password="y7wdPV46XtnQevmJ", host="gz.tystnad.tech",
                                      port="42345", database="fillexcel")
        cursor = connection.cursor()
        # Executing a SQL query to insert data into table
        insert_query = f"""insert into public.file_record 
        (id, created_at, updated_at, username, file_id, filename, requirement_id)
        values ({SnowFlake(0, 0).next_id()}, now(), now(), '{username}', '{file_id}', '{filename}', {requirement_id})
        """
        cursor.execute(insert_query)
        # Commit changes to the database
        connection.commit()
        cursor.close()
        connection.close()
        log.info(f'saved record {requirement_id}: {file_id}, {filename}')
    except (Exception, psycopg2.Error) as error:
        log.error("Failed to insert record into table " + str(error))
