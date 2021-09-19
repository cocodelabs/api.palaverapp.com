import json
import os
from typing import Optional

import peewee
import redis
from apns2.client import NotificationPriority
from rivr.http import Request, Response
from rivr.views import View
from rq import Queue

from palaverapi.decorators import requires_body
from palaverapi.message import Message
from palaverapi.models import Token
from palaverapi.responses import ProblemResponse
from palaverapi.utils import send_notification
from palaverapi.views.mixins import PermissionRequiredMixin

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_client = redis.from_url(redis_url)
queue = Queue(connection=redis_client)


def handle_request(
    attributes,
    token: Token,
    ttl: Optional[int],
    priority: Optional[NotificationPriority] = None,
) -> Response:
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
        kwargs=dict(priority=priority),
    )

    return Response(status=202)


class PushViewRFC(View):
    def post(self, request: Request, subscription_id: str) -> Response:
        content_type = (request.content_type or 'application/octet-stream').split(';')[0]

        if content_type == 'application/json':
            body = request.body.read()
            content = body.decode('utf-8')
            attributes = json.loads(content)
        elif content_type == 'text/irc':
            body = request.body.read()

            # FIXME assuming utf-8 charset, check parameters
            content = body.decode('utf-8').strip()

            message = Message.parse(content)
            if message.command not in ('PRIVMSG', 'NOTICE'):
                return ProblemResponse(400, f'Command {message.command} is not supported')

            if len(message.parameters) != 2:
                return ProblemResponse(400, f'{message.command} takes two parameters')

            attributes = {
                'message': message.get(1),
            }

            if message.prefix:
                attributes['sender'] = message.prefix.partition('!')[0]

            target = message.get(0)
            if target and target.startswith('#'):
                # no access to 005 assume # is only channel prefix
                attributes['channel'] = target

            if message.prefix:
                attributes['sender'] = message.prefix.partition('!')[0]

        else:
            return ProblemResponse(415, f'Unsupported media type {content_type}')

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

        if ttl == 0:
            # rq requires >0 ttl
            ttl = 1

        if 'Topic' in request.headers:
            return ProblemResponse(400, 'Topic is not supported. Remove Topic header.')

        prefer = request.headers['Prefer']
        if prefer and prefer != 'respond-async':
            return ProblemResponse(400, f'Prefer {prefer} is unsupported.')

        urgency = request.headers.get('Urgency', 'normal')
        if urgency not in ('low', 'normal'):
            return ProblemResponse(400, f'Urgency {urgency} is unsupported.')

        priority: NotificationPriority
        if urgency == 'low':
            priority = NotificationPriority.Delayed
        else:
            priority = NotificationPriority.Immediate

        return handle_request(attributes, token, ttl, priority=priority)


class PushView(PermissionRequiredMixin, View):
    scope_required = 'push'

    @requires_body
    def post(self, request: Request, attributes) -> Response:
        token = self.get_token()
        if not token:
            return ProblemResponse(401, 'Unauthorized')

        return handle_request(attributes, token, None)
