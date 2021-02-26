from functools import wraps
from typing import Callable

from rivr.http import Response

from palaverapi.responses import ProblemResponse


def requires_body(func: Callable[..., Response]):
    @wraps(func)
    def wrapper(self, request) -> Response:
        try:
            body = request.attributes
        except (UnicodeDecodeError, ValueError):
            return ProblemResponse(400, 'Invalid request body')

        return func(self, request, body)

    return wrapper
