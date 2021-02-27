import json
from functools import wraps
from typing import Callable
from urllib.parse import parse_qsl

from rivr.http import Request, Response

from palaverapi.responses import ProblemResponse


def requires_body(func: Callable[..., Response]):
    @wraps(func)
    def wrapper(self, request: Request) -> Response:
        if request.content_type:
            content = request.body.read()
            content_type = request.content_type.split(';')[0]

            try:
                if content_type == 'application/json':
                    content = content.decode('utf-8')
                    body = json.loads(content)
                elif content_type == 'application/x-www-form-urlencoded':
                    content = content.decode('utf-8')
                    data = parse_qsl(content, True)
                    body = dict((k, v) for k, v in data)
                else:
                    return ProblemResponse(415, 'Unsupported Media Type')
            except (UnicodeDecodeError, ValueError):
                return ProblemResponse(400, 'Invalid request body')

            return func(self, request, body)

        return func(self, request, {})

    return wrapper
