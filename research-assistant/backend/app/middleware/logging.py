import time

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging  import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()

        logger.info(
            f"{request.method} {request.url.path} started"
        )

        response = await call_next(request)

        duration = (time.perf_counter() - start) * 1000

        logger.info(
            f"{request.method} {request.url.path} "
            f"{response.status_code} "
            f"{duration:.2f}ms"
        )

        return response