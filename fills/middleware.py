import logging

from django.http import HttpRequest, JsonResponse
from django.middleware.common import MiddlewareMixin

log = logging.getLogger(__name__)


class ErrorHandlerMiddleware(MiddlewareMixin):
    """捕获报错的异常并返回统一结构的数据"""

    @staticmethod
    def process_exception(request: HttpRequest, exception):
        error_message = str(exception)
        error_data = {
            'data': tuple(),
            'path': request.get_full_path(),
            'message': error_message
        }
        log.error(error_data)
        return JsonResponse(error_data, status=500)


class ModifyServerHeaderMiddleware(MiddlewareMixin):
    """修改响应头，不显示服务器的版本号"""
    @staticmethod
    def process_response(_, response):
        if hasattr(response, 'headers'):
            try:
                response.headers.__setitem__('Server', 'WSGIServer')
            finally:
                pass
        return response
