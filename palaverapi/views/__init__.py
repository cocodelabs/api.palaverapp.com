import json
import logging
import sys

import redis
from rivr.http import Request, Response

from palaverapi.responses import ProblemResponse
from palaverapi.views.push import redis_client


def handle_error(request: Request, exception: Exception):
    logger = logging.getLogger('rivr.request')
    logger.error(exception, exc_info=sys.exc_info())
    return ProblemResponse(500, 'Internal Server Error')


def is_redis_available() -> bool:
    try:
        redis_client.ping()
    except redis.exceptions.ConnectionError:
        return False

    return True


def index(request: Request) -> Response:
    return Response(status=204)


def status(request) -> Response:
    if is_redis_available:
        return Response(
            json.dumps(
                {
                    'status': 'pass',
                }
            ),
            content_type='application/health+json',
        )

    return Response(
        json.dumps(
            {
                'status': 'fail',
            }
        ),
        status=504,
        content_type='application/health+json',
    )


def crash(request: Request) -> Response:
    raise RuntimeError("You are eaten by a grue")
