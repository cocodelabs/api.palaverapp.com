import json
from typing import Optional

from rivr.http import Request, Response


class ProblemResponse(Response):
    def __init__(self, status, title=None):
        content = json.dumps({'title': title})
        super(ProblemResponse, self).__init__(
            content=content, status=status, content_type='application/problem+json'
        )


class RESTResponse(Response):
    def __init__(self, request: Request, payload, status: Optional[int] = None):
        content = json.dumps(payload)
        content_type = 'application/json'

        super(RESTResponse, self).__init__(content, status, content_type)
