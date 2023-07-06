"""
Django settings for fillexcel project.

Generated by 'django-admin startproject' using Django 4.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from datetime import datetime, timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-fmhqgp5l666@46so9qb!ye^b#e&$#g+)ckop4m#o-9dmr6^)7o'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ()

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "fills.apps.FillsConfig",
    'rest_framework',
    'rest_framework_simplejwt'
)

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'fills.middleware.ErrorHandlerMiddleware'
)

ROOT_URLCONF = 'fillexcel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': (),
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': (
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages'
            )
        }
    }
]

WSGI_APPLICATION = 'fillexcel.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'fillexcel',
        'USER': 'fillexcel',
        'PASSWORD': 'y7wdPV46XtnQevmJ',
        'HOST': 'gz.tystnad.tech',  # 如果数据库在本地，请填写本机 IP 地址或者 localhost
        'PORT': '42345',  # 默认端口号是 5432
        "TEST": {
            "NAME": "test_fillexcel"
        }
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://default:ZI6vLhsHdKCjeiyw@gz.tystnad.tech:46379/2',
        'TIMEOUT': 60 * 60
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = (
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    }
)

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

DATETIME_FORMAT = 'Y年m月d日 H:i:s'

DATE_FORMAT = 'Y年m月d日'

USE_I18N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 创建log文件的文件夹
LOG_DIR = BASE_DIR / 'var' / 'logs'
if not LOG_DIR.exists():
    LOG_DIR.mkdir(parents=True)

# 基本配置，可以复用的
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # 禁用已经存在的logger实例
    'filters': {'require_debug_false': {'()': 'django.utils.log.RequireDebugFalse'}},
    'formatters': {  # 定义了两种日志格式
        'verbose': {  # 详细
            'format': '%(asctime)s %(levelname)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
        'simple': {  # 简单
            'format': '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s'
        },
    },
    'handlers': {  # 定义了三种日志处理方式
        'file': {  # 对INFO级别以上信息以日志文件形式保存
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',  # 滚动生成日志，切割
            'filename': LOG_DIR / 'django.log',  # 日志文件名
            'maxBytes': 1024 * 1024 * 8,  # 单个日志文件最大为8M
            'backupCount': 7,  # 日志备份文件最大数量
            'formatter': 'simple',  # 简单格式
            'encoding': 'utf-8'  # 防止中文乱码
        },
        'sql': {  # django 执行的sql记录
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',  # 滚动生成日志，切割
            'filename': LOG_DIR / 'django-sql.log',  # 日志文件名
            'maxBytes': 1024 * 1024 * 8,  # 单个日志文件最大为8M
            'backupCount': 7,  # 日志备份文件最大数量
            'formatter': 'simple',  # 简单格式
            'encoding': 'utf-8'  # 防止中文乱码
        },
        'console': {  # 打印到终端console
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console', 'sql'],
            'level': 'DEBUG',
            'propagate': True
        }
    },
    'root': {'level': 'INFO', 'handlers': ('console', 'file')}
}

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'PAGE_SIZE': 8
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=4),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1)
}
