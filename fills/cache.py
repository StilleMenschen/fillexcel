import logging
from functools import wraps

from django.core.cache import cache
from rest_framework.response import Response

log = logging.getLogger(__name__)


class CacheManager:
    # 缓存前缀
    cache_prefix = 'default'

    @property
    def prefix(self):
        """
        在继承类中查找 cache_prefix 作为缓存 key 的前缀
        """
        return getattr(self, 'cache_prefix')

    def get_cache(self, pk: int | str, query):
        """
        :param pk 数据库对象主键
        :param query 读取数据库的无参数函数
        """
        cache_key = f'{self.prefix}:{pk}'
        val = cache.get(cache_key, None)
        if val:
            return val
        else:
            val = query()
            cache.set(cache_key, val)
            log.info('<CacheManager> store key: ' + cache_key)
            return val

    def invalid_cache(self, pk: int | str):
        """
        :param pk 数据库对象主键
        """
        cache_key = f'{self.prefix}:{pk}'
        val = cache.get(cache_key, None)
        if val:
            log.info('<CacheManager> delete key: ' + cache_key)
            cache.delete(cache_key)


def cacheable(cache_key: str | int = None):
    """
    装饰器，用于缓存响应。
    """

    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            # 生成缓存键
            key = "{}:{}".format(self.__class__.__name__, kwargs.get(str(cache_key), 'none'))

            cached_response = cache.get(key)

            if cached_response:
                return Response(cached_response, status=200)

            # 调用实际的视图方法
            response: Response = method(self, *args, **kwargs)

            if response.status_code <= 299 and response.data:
                log.info('<cache_response> store key: ' + key)
                # 将响应内容存入缓存
                cache.set(key, response.data)

            return response

        return wrapper

    return decorator


def cache_evict(cache_key: str | int = None):
    """
    装饰器，用于清理缓存的响应。
    """

    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            # 生成缓存键
            key = "{}:{}".format(self.__class__.__name__, kwargs.get(str(cache_key), 'none'))

            cached_response = cache.get(key)

            if cached_response:
                log.info('<cache_response> delete key: ' + key)
                cache.delete(key)

            # 调用实际的视图方法
            return method(self, *args, **kwargs)

        return wrapper

    return decorator
