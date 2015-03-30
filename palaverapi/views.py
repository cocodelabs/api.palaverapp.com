import hashlib
import os

import redis
from rq import Queue
import peewee

from rivr.router import Router
from rivr.http import Response, RESTResponse
from rivr.views import RESTView

from palaverapi.models import database, Device, Token
from palaverapi.utils import send_notification


router = Router()
app = router

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
redis = redis.from_url(redis_url)
queue = Queue(connection=redis)


@router.register(r'^$')
def status(request):
    return Response(status=204)


class RegisterView(RESTView):
    def post(self, request):
        apns_token = request.POST['device_token']
        push_token = hashlib.sha1(hashlib.sha1(apns_token + apns_token).hexdigest()).hexdigest()
        status = 200

        try:
            with database.transaction():
                device = Device.create(apns_token=apns_token)
            status = 201
        except peewee.IntegrityError:
            device = Device.get(apns_token=apns_token)

        try:
            with database.transaction():
                token = Token.create(device=device, token=apns_token, scope=Token.ALL_SCOPE)
        except peewee.IntegrityError:
            token = Token.get(device=device, token=apns_token)

        try:
            with database.transaction():
                push = Token.create(device=device, token=push_token, scope=Token.PUSH_SCOPE)
        except peewee.IntegrityError:
            push = Token.get(device=device, token=push_token)

        return RESTResponse(request, {
            'device_token': apns_token,
            'push_token': push_token,
        }, status=status)


router.register(r'^1/devices$', database(RegisterView.as_view()))


class PushView(RESTView):
    def get_token(self):
        authorization = self.request.headers.get('AUTHORIZATION', None)
        if not authorization:
            return

        if authorization:
            _, access_token = authorization.split(' ', 2)

        try:
            token = Token.get(token=access_token)
        except Token.DoesNotExist:
            token = None

        return token

    def post(self, request):
        try:
            attributes = request.POST
        except UnicodeDecodeError, ValueError:
            return Response(status=400)

        message = attributes.get('message', None)
        sender = attributes.get('sender', None)
        channel = attributes.get('channel', None)
        network = attributes.get('network', None)
        badge = int(attributes.get('badge', 1))

        with database:
            token = self.get_token()
            if not token:
                return Response(status=401)

            queue.enqueue(send_notification, token.device.apns_token, message, sender, channel, badge, network)

        return Response(status=202)

router.register(r'^1/push$', PushView.as_view())

