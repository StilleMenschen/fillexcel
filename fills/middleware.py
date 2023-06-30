import logging

from django.http import JsonResponse
from django.middleware.common import MiddlewareMixin

log = logging.getLogger(__name__)


class ErrorHandlerMiddleware(MiddlewareMixin):

    @staticmethod
    def process_exception(request, exception):
        error_message = str(exception)
        error_data = {
            'error': error_message
        }
        log.error(error_message)
        return JsonResponse(error_data, status=500)
