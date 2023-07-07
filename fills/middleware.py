import logging

from django.http import HttpRequest, JsonResponse
from django.middleware.common import MiddlewareMixin

log = logging.getLogger(__name__)


class ErrorHandlerMiddleware(MiddlewareMixin):

    @staticmethod
    def process_exception(request: HttpRequest, exception):
        error_message = str(exception)
        error_data = {
            'path': request.get_full_path(),
            'error': error_message
        }
        log.error(error_data)
        return JsonResponse(error_data, status=500)


class ModifyServerHeaderMiddleware(MiddlewareMixin):
    @staticmethod
    def process_response(_, response):
        if hasattr(response, 'headers'):
            try:
                response.headers.__setitem__('Server', 'WSGIServer')
            finally:
                pass
        return response
