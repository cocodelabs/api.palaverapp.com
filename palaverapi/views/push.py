import os
from typing import Optional

import peewee
import redis
from rivr.http import Request, Response
from rivr.views import View
from rq import Queue

from palaverapi.decorators import requires_body
from palaverapi.models import Token
from palaverapi.responses import ProblemResponse
from palaverapi.utils import send_notification
from palaverapi.views.mixins import PermissionRequiredMixin

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_client = redis.from_url(redis_url)
queue = Queue(connection=redis_client)


def handle_request(attributes, token: Token, ttl: Optional[int]) -> Response:
    message = attributes.get('message', None)
    sender = attributes.get('sender', None)
    channel = attributes.get('channel', None)
    network = attributes.get('network', None)
    badge = int(attributes.get('badge', 1))
    intent = attributes.get('intent', None)
    private = attributes.get('private', False)

    if (
        'private' not in attributes
        and 'badge' not in attributes
        and 'message' not in attributes
    ):
        return ProblemResponse(422, 'Missing payload, set private, badge or message')

    queue.enqueue(
        send_notification,
        ttl=ttl,
        args=(
            token.device.apns_token,
            message,
            sender,
            channel,
            badge,
            network,
            intent,
            private,
        ),
    )

    return Response(status=202)


class PushViewRFC(View):
    @requires_body
    def post(self, request: Request, attributes, subscription_id: str) -> Response:
        try:
            token = Token.get(token=subscription_id)
        except Token.DoesNotExist:
            return ProblemResponse(404, 'Not Found')

        if token.scope != Token.PUSH_SCOPE:
            return ProblemResponse(404, 'Not Found')

        ttl_string = request.headers['TTL']
        if not ttl_string:
            return ProblemResponse(400, 'TTL header is required')

        try:
            ttl = int(ttl_string)
        except ValueError:
            return ProblemResponse(400, 'TTL must be a number')

        if ttl < 0:
            return ProblemResponse(400, 'TTL must be a positive number')

        if 'Topic' in request.headers:
            return ProblemResponse(400, 'Topic is not supported. Remove Topic header.')

        prefer = request.headers['Prefer']
        if prefer and prefer != 'respond-async':
            return ProblemResponse(400, f'Prefer {prefer} is unsupported.')

        urgency = request.headers['Urgency']
        if urgency and urgency != 'normal':
            return ProblemResponse(400, f'Urgency {urgency} is unsupported.')

        return handle_request(attributes, token, ttl)


class PushView(PermissionRequiredMixin, View):
    scope_required = 'push'

    @requires_body
    def post(self, request: Request, attributes) -> Response:
        token = self.get_token()
        if not token:
            return ProblemResponse(401, 'Unauthorized')

        return handle_request(attributes, token, None)
