import os
import uuid

from minio import Minio

from .logger import init_logger
from .configurator import read_minio_config

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

    def __init__(self):
        config = read_minio_config()
        self.bucket = config['bucket']
        del config['bucket']
        self.client = Minio(**config)
        found = self.client.bucket_exists(self.bucket)
        if not found:
            self.client.make_bucket(self.bucket)
            print(f"Bucket '{self.bucket}' created")

    def store_file(self, file_path):
        p = convert_path(file_path)
        filename = f'{uuid.uuid1().hex}'
        obj = self.client.fput_object(
            self.bucket, filename, p,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        log.info(f'save object {file_path} to {filename}, etag {obj.etag}')
        return filename

    def get_file(self, file_id) -> bytes:
        obj = self.client.get_object('fills', file_id)
        return obj.data

    def remove_file(self, file_id):
        self.client.remove_object('fills', file_id)


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
