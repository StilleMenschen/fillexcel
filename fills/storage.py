import os
import uuid

import certifi
import urllib3
from minio import Minio

from fillexcel.configurator import read_minio_config
from .logger import init_logger

log = init_logger(__name__, 'storage.log')


def convert_path(path):
    """Convert path-like object to string.

    On python <= 3.5 the input argument is always returned unchanged
    (no support for path-like objects available).
    """
    if hasattr(os, "PathLike") and isinstance(path, os.PathLike):
        return os.fspath(path)
    else:
        return path


class Storage:

    def __init__(self, retry=4):
        """对象存储
        retry: 重试次数
        """
        timeout = 30  # 30 秒请求超时
        ca_certs = os.environ.get('SSL_CERT_FILE') or certifi.where()
        http_client = urllib3.PoolManager(
            timeout=urllib3.util.Timeout(connect=timeout, read=timeout),
            maxsize=10,
            cert_reqs='CERT_REQUIRED',
            ca_certs=ca_certs,
            retries=urllib3.Retry(
                total=retry,
                backoff_factor=0.2,
                status_forcelist=[500, 502, 503, 504]
            )
        )
        config = read_minio_config()
        # 没有则创建存储桶
        self.bucket = config['bucket']
        del config['bucket']
        self.client = Minio(http_client=http_client, **config)
        found = self.client.bucket_exists(self.bucket)
        if not found:
            self.client.make_bucket(self.bucket)
            print(f"Bucket '{self.bucket}' created")

    def store_object_for_path(self, hash_id, file_path, folder=None, content_type=None):
        """存储对应路径的文件

        file_path: 文件路径
        folder: 对象存储的文件夹
        content_type: 内容类型，默认 application/octet-stream
        """
        p = convert_path(file_path)
        if folder:
            filename = f'{folder}/{hash_id}'
        else:
            filename = hash_id
        if content_type:
            obj = self.client.fput_object(self.bucket, filename, p, content_type)
        else:
            obj = self.client.fput_object(self.bucket, filename, p)

        log.info(f'save object {file_path} to {filename}, etag {obj.etag}')
        return filename

    def store_object(self, hash_id, file, size, folder=None, content_type=None):
        """直接存储文件

        file: 文件，有 read() 方法
        size: 文件大小
        folder: 对象存储的文件夹
        content_type: 内容类型，默认 application/octet-stream
        """
        if folder:
            filename = f'{folder}/{hash_id}'
        else:
            filename = hash_id
        if content_type:
            obj = self.client.put_object(self.bucket, filename, file, size, content_type)
        else:
            obj = self.client.put_object(self.bucket, filename, file, size)
        log.info(f'save object {file} to {filename}, etag {obj.etag}')
        return hash_id

    def get_object(self, file_id, folder=None) -> bytes:
        """获得文件字节

        folder: 对象存储的文件夹
        """
        if folder:
            obj = self.client.get_object(self.bucket, f'{folder}/{file_id}')
        else:
            obj = self.client.get_object(self.bucket, file_id)
        return obj.data

    def get_object_to_path(self, file_id, fspath, folder=None):
        """获得文件并保存到指定路径

        fspath: 存储的路径
        folder: 对象存储的文件夹
        """
        if folder:
            self.client.fget_object(self.bucket, f'{folder}/{file_id}', fspath)
        else:
            self.client.fget_object(self.bucket, file_id, fspath)

    def remove_object(self, file_id, folder=None):
        if folder:
            self.client.remove_object(self.bucket, f'{folder}/{file_id}')
        else:
            self.client.remove_object(self.bucket, file_id)


def main():
    server_config = {
        "url": "http://localhost:9090/api/v1/service-account-credentials",
        "accessKey": "zNpKlffFio4cBZxRxjoO",
        "secretKey": "EVwOLLwzzQNhAmPWJm6WF1ha4VDR2VNi8rDL4IXk",
        "api": "s3v4",
        "path": "auto"
    }
    # Create a client with the MinIO server playground, its access key
    # and secret key.
    client = Minio(
        "localhost:9000",
        access_key=server_config['accessKey'],
        secret_key=server_config['secretKey'],
        secure=False
    )

    # Make 'fills' bucket if not exist.
    found = client.bucket_exists("fills")
    if not found:
        client.make_bucket("fills")
    else:
        print("Bucket 'fills' already exists")

    # Upload '1688786211006663400-abc.xlsx' as object name
    # 'asiaphotos-2015.xlsx' to bucket 'fills'.
    filename = f'test/{uuid.uuid1().hex}.xlsx'
    obj = client.fput_object(
        "fills", filename, r"D:\PythonProjects\fillexcel\fills\1688786211006663400-abc.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    print(obj.etag)
    print(obj.object_name)
    print(
        "'1688786211006663400-abc.xlsx' is successfully uploaded as "
        f"object {filename} to bucket 'fills'."
    )
    objects = client.list_objects("fills")
    for obj in objects:
        print(obj.bucket_name)
        print(obj.object_name)
        print(obj.size)

    client.fget_object('fills', filename, fr"D:\opt\{filename}.xlsx")
    obj = client.get_object('fills', filename)
    print(obj.data)
    client.remove_object('fills', filename)
    client.stat_object('fills', '4dfd907e1e3011ee94c82cf05dddedd1')
