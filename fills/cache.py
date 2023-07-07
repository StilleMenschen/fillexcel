import logging

from django.core.cache import cache

log = logging.getLogger(__name__)


class CacheManager:
    # 缓存前缀
    cache_prefix = 'none'

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
