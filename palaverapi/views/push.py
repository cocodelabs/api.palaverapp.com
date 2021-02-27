import os

import peewee
import redis
from rivr.http import Response
from rq import Queue

from palaverapi.decorators import requires_body
from palaverapi.responses import ProblemResponse
from palaverapi.rest_view import RESTView
from palaverapi.utils import send_notification
from palaverapi.views.mixins import PermissionRequiredMixin

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis = redis.from_url(redis_url)
queue = Queue(connection=redis)


class PushView(PermissionRequiredMixin, RESTView):
    scope_required = 'push'

    @requires_body
    def post(self, request, attributes):
        message = attributes.get('message', None)
        sender = attributes.get('sender', None)
        channel = attributes.get('channel', None)
        network = attributes.get('network', None)
        badge = int(attributes.get('badge', 1))
        intent = attributes.get('intent', None)
        private = attributes.get('private', False)

        token = self.get_token()
        if not token:
            return ProblemResponse(401, 'Unauthorized')

        queue.enqueue(
            send_notification,
            token.device.apns_token,
            message,
            sender,
            channel,
            badge,
            network,
            intent,
            private,
        )

        return Response(status=202)
