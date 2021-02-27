import json
import logging
import sys

from rivr.http import Response

from palaverapi.responses import ProblemResponse
from palaverapi.views.push import redis


def handle_error(request, exception):
    logger = logging.getLogger('rivr.request')
    logger.error(exception, exc_info=sys.exc_info())
    return ProblemResponse(500, 'Internal Server Error')


def is_redis_available():
    try:
        redis.ping()
    except redis.exceptions.ConnectionError:
        return False

    return True


def index(request):
    return Response(status=204)


def status(request):
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


def crash(request):
    raise RuntimeError("You are eaten by a grue")
