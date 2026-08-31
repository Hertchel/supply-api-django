import time
import logging

logger = logging.getLogger(__name__)


class RequestTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()

        response = self.get_response(request)

        duration = time.perf_counter() - start_time

        logger.warning(
            "REQUEST TIMING: %s %s -> %s in %.3f seconds",
            request.method,
            request.get_full_path(),
            response.status_code,
            duration,
        )

        return response