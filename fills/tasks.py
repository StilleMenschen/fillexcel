import os
import pathlib
import tempfile
import time

import psycopg2
import xlwings as xw
from celery import Celery

from fillexcel.configurator import read_postgres_config, read_celery_config
from .logger import init_logger
from .storage import Storage
from .utils import SnowFlake

app = Celery('fills', **read_celery_config())

log = init_logger(__name__, 'celery-task.log')


# celery -A fills.tasks worker -l INFO -c 2 -P eventlet

@app.task
def write_to_excel(data_for_fill: dict):
    t0 = time.perf_counter()
    # 下载文件到临时目录
    tempdir = tempfile.TemporaryDirectory()
    tmp_dir = pathlib.Path(tempdir.name)
    filename = add_timestamp_for_filename(data_for_fill['filename'])
    save_path = tmp_dir / filename
    try:
        storge = Storage()
        storge.get_object_to_path(data_for_fill['fileId'], str(save_path), 'requirement')
    except Exception as e:
        tempdir.cleanup()
        log.error(str(e))
        return False
    # 填入数据
    start_line = data_for_fill['startLine']
    excel_data: dict = data_for_fill['data']
    excel_app = xw.App(visible=False, add_book=False)
    book = excel_app.books.open(save_path)
    sheet = book.sheets.active
    for column, data_list in excel_data.items():
        range_len = len(data_list)
        sheet.range(f'{column}{start_line}').value = tuple((v,) for v in data_list)
        # 设置格式为文本
        sheet.range(f'{column}{start_line}:{column}{start_line + range_len}').number_format = '@'
    book.save()
    book.close()
    excel_app.quit()
    del data_for_fill['data']
    try:
        # 上传写入后的文件
        file_id = storge.store_object_for_path(
            save_path, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        log.error(str(e))
        return False
    finally:
        tempdir.cleanup()
    # 文件生成记录
    save_record(data_for_fill['requirementId'], data_for_fill['username'], file_id, filename)
    del data_for_fill
    log.info(f'elapsed time {time.perf_counter() - t0}')
    return filename


def add_timestamp_for_filename(filename=None):
    if not filename:
        return filename
    filename, ext = os.path.splitext(filename)
    return f"{filename}-{time.time_ns()}{ext}"


def save_record(requirement_id, username, file_id, filename):
    try:
        connection = psycopg2.connect(**read_postgres_config())
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
