import os
import pathlib
import tempfile
import time

import psycopg2
import openpyxl
from celery import Celery

from fillexcel.configurator import read_postgres_config, read_celery_config
from .logger import init_logger
from .storage import Storage
from .utils import SnowFlake

app = Celery('fills', **read_celery_config())

log = init_logger(__name__, 'celery-task.log')


# celery -A fills.tasks worker -l INFO -c 2 -P eventlet

def excel_column_to_number(column):
    result = 0
    for i in range(len(column)):
        result = result * 26 + ord(column[i]) - ord('A') + 1
    return result


def foreach_rows(worksheet, start_line, excel_data: dict):
    for column, data_list in excel_data.items():
        for num, val in zip(range(start_line, start_line + len(data_list)), data_list):
            worksheet[f'{column}{num}'] = str(val)
            worksheet[f'{column}{num}'].number_format = '@'


@app.task
def write_to_excel(data_for_fill: dict):
    """[定时任务] 写入数据到 Excel

    :param data_for_fill 待写入的数据
    """
    t0 = time.perf_counter()
    # 创建操作系统支持的临时目录
    tempdir = tempfile.TemporaryDirectory()
    tmp_dir = pathlib.Path(tempdir.name)
    filename = add_timestamp_for_filename(data_for_fill['filename'])
    save_path = tmp_dir / filename
    try:
        storge = Storage()
        # 下载文件到临时目录
        storge.get_object_to_path(data_for_fill['fileId'], str(save_path), 'requirement')
    except Exception as e:
        # 清空缓存文件
        tempdir.cleanup()
        log.error(str(e))
        return False
    # 填入数据
    start_line = data_for_fill['startLine']
    excel_data: dict = data_for_fill['data']
    book = openpyxl.load_workbook(str(save_path))
    sheet = book.active
    foreach_rows(sheet, start_line, excel_data)
    book.save(str(save_path))
    book.close()
    del data_for_fill['data']
    try:
        # 上传写入后的文件
        storge.store_object_for_path(data_for_fill['hashId'], save_path,
                                     content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        log.error(str(e))
        return False
    finally:
        # 清空缓存文件
        tempdir.cleanup()
    # 文件生成记录
    save_record(data_for_fill['requirementId'], data_for_fill['username'], data_for_fill['hashId'], filename)
    del data_for_fill
    log.info(f'elapsed time {time.perf_counter() - t0}')
    return filename


def add_timestamp_for_filename(filename=None):
    """为文件名加上时间戳"""
    if not filename:
        return filename
    filename, ext = os.path.splitext(filename)
    return f"{filename}-{time.time_ns()}{ext}"


def save_record(requirement_id, username, file_id, filename):
    """写入生成记录到数据库"""
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
