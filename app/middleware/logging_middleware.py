from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.utils.logger import logger
from app.utils.metrics import record_request
import time


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()

        logger.debug(
            f"Incoming request | method={request.method} | path={request.url.path}"
        )

        try:
            response = await call_next(request)
            duration = round(time.time() - start, 4)

            record_request(
                status_code=response.status_code,
                response_time=duration,
                path=request.url.path,
                method=request.method
            )

            if response.status_code >= 500:
                logger.error(
                    f"Response | method={request.method} | path={request.url.path} "
                    f"| status={response.status_code} | time={duration}s"
                )
            elif response.status_code >= 400:
                logger.warning(
                    f"Response | method={request.method} | path={request.url.path} "
                    f"| status={response.status_code} | time={duration}s"
                )
            else:
                logger.info(
                    f"Response | method={request.method} | path={request.url.path} "
                    f"| status={response.status_code} | time={duration}s"
                )

            return response

        except Exception as e:
            duration = round(time.time() - start, 4)

            record_request(
                status_code=500,
                response_time=duration,
                path=request.url.path,
                method=request.method
            )

            logger.critical(
                f"Unhandled exception | method={request.method} | path={request.url.path} "
                f"| status=500 | time={duration}s | error={str(e)}",
                exc_info=True
            )

            raise