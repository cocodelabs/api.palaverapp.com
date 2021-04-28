import json
from functools import wraps
from typing import Callable
from urllib.parse import parse_qsl

from rivr.http import Request, Response

from palaverapi.responses import ProblemResponse


def requires_body(func: Callable[..., Response]):
    @wraps(func)
    def wrapper(self, request: Request, *args, **kwargs) -> Response:
        if request.content_type:
            body = request.body.read()
            content_type = request.content_type.split(';')[0]

            try:
                if content_type == 'application/json':
                    content = body.decode('utf-8')
                    payload = json.loads(content)
                elif content_type == 'application/x-www-form-urlencoded':
                    content = body.decode('utf-8')
                    data = parse_qsl(content, True)
                    payload = dict((k, v) for k, v in data)
                else:
                    return ProblemResponse(415, 'Unsupported Media Type')
            except (UnicodeDecodeError, ValueError):
                return ProblemResponse(400, 'Invalid request body')

            return func(self, request, *args, payload, **kwargs)

        return func(self, request, *args, {}, **kwargs)

    return wrapper
