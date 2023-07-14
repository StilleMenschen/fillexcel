import pathlib
from configparser import ConfigParser
from configparser import ExtendedInterpolation

CURRENT_DIR = pathlib.Path(__file__).parent


def read_postgres_config():
    config = ConfigParser(allow_no_value=True,
                          interpolation=ExtendedInterpolation())
    config.read(CURRENT_DIR / 'configure.ini', encoding='utf8')
    return config['postgres']


def read_minio_config():
    config = ConfigParser(allow_no_value=True,
                          interpolation=ExtendedInterpolation())
    config.read(CURRENT_DIR / 'configure.ini', encoding='utf8')
    c = config['minio']
    return {
        'endpoint': c['endpoint'],
        'access_key': c['access'],
        'secret_key': c['secret'],
        'secure': True if c['secure'] == 'true' else False,
        'bucket': c['bucket']
    }


def read_celery_config():
    config = ConfigParser(allow_no_value=True,
                          interpolation=ExtendedInterpolation())
    config.read(CURRENT_DIR / 'configure.ini', encoding='utf8')
    return config['celery']
