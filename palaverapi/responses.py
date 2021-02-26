import json

from rivr.response import Response


class ProblemResponse(Response):
    def __init__(self, status, title=None):
        content = json.dumps({'title': title})
        super(ProblemResponse, self).__init__(
            content=content, status=status, content_type='application/problem+json'
        )
