import hashlib
import uuid
import os
import sys
import json
import logging

import redis
from rq import Queue
import peewee

from rivr.http import Http404, Response

from palaverapi.rest_view import RESTView
from palaverapi.models import database, Device, Token
from palaverapi.responses import ProblemResponse, RESTResponse
from palaverapi.utils import send_notification
from palaverapi.decorators import requires_body


def handle_error(request, exception):
    logger = logging.getLogger('rivr.request')
    logger.error(exception, exc_info=sys.exc_info())
    return ProblemResponse(500, 'Internal Server Error')


redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis = redis.from_url(redis_url)
queue = Queue(connection=redis)


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


class RegisterView(RESTView):
    @requires_body
    def post(self, request, attributes):
        apns_token = attributes['device_token']
        bytes_token = apns_token.encode('utf-8')
        push_token = hashlib.sha1(
            hashlib.sha1(bytes_token + bytes_token).hexdigest().encode('utf-8')
        ).hexdigest()
        status = 200

        try:
            with database.transaction():
                device = Device.create(apns_token=apns_token)
            status = 201
        except peewee.IntegrityError:
            device = Device.get(apns_token=apns_token)

        try:
            with database.transaction():
                token = Token.create(
                    device=device, token=apns_token, scope=Token.ALL_SCOPE
                )
        except peewee.IntegrityError:
            token = Token.get(device=device, token=apns_token)

        try:
            with database.transaction():
                push = Token.create(
                    device=device, token=push_token, scope=Token.PUSH_SCOPE
                )
        except peewee.IntegrityError:
            push = Token.get(device=device, token=push_token)

        return RESTResponse(
            request,
            {
                'device_token': apns_token,
                'push_token': push_token,
            },
            status=status,
        )


class PermissionRequiredMixin(object):
    scope_required = 'all'

    def get_token(self):
        authorization = self.request.headers.get('AUTHORIZATION', None)
        if not authorization or (authorization and ' ' not in authorization):
            return

        if authorization:
            _, access_token = authorization.split(' ', 2)

        try:
            token = Token.get(token=access_token)
        except Token.DoesNotExist:
            token = None

        return token

    def has_permission(self):
        self.token = self.get_token()
        return self.token and (
            self.token.scope == 'all' or self.token.scope == self.scope_required
        )

    def handle_no_permission(self):
        return ProblemResponse(401, 'Unauthorized')

    def dispatch(self, request, *args, **kwargs):
        self.request = request

        if not self.has_permission():
            return self.handle_no_permission()

        return super(PermissionRequiredMixin, self).dispatch(request, *args, **kwargs)


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


class DeviceDetailView(PermissionRequiredMixin, RESTView):
    http_method_names = ['options', 'head', 'get', 'delete', 'patch']

    def get(self, request):
        device = self.token.device
        return RESTResponse(
            request,
            {
                'apns_token': device.apns_token,
            },
        )

    @requires_body
    def patch(self, request, attributes):
        device = self.token.device
        device.apns_token = attributes['apns_token']
        device.save()
        return Response(status=204)

    def delete(self, request):
        device = self.token.device
        device.delete_instance(recursive=True)

        return Response(status=204)


def serialise_authorisation(token):
    return {
        'url': '/authorisations/{}'.format(token.token_last_eight),
        'token_last_eight': token.token_last_eight,
        'scopes': [token.scope],
    }


class AuthorisationListView(PermissionRequiredMixin, RESTView):
    def get(self, request):
        tokens = Token.select().where(Token.device == self.token.device)
        return [serialise_authorisation(token) for token in tokens]

    @requires_body
    def post(self, request, attributes):
        scopes = attributes.get('scopes', None)
        scope = Token.ALL_SCOPE
        if scopes and len(scopes) == 1:
            if scopes[0] == Token.ALL_SCOPE or scopes[0] == Token.PUSH_SCOPE:
                scope = scopes[0]

        token = attributes.get('token', None)
        if token is None or not len(token) > 20:
            token = str(uuid.uuid4())

        status = 201
        try:
            with database.transaction():
                Token.create(device=self.token.device, token=token, scope=scope)
        except peewee.IntegrityError:
            status = 200

            try:
                t = Token.get(device=self.token.device, token=token)
            except Token.DoesNotExist:
                return ProblemResponse(403, 'Access Denied')

            if t.scope != scope:
                t.scope = scope
                t.save()

        attributes = serialise_authorisation(self.token)
        attributes['token'] = token
        return RESTResponse(request, attributes, status=status)


class AuthorisationDetailView(PermissionRequiredMixin, RESTView):
    def get_authorisation(self, token_last_eight):
        try:
            return (
                Token.select()
                .where(
                    Token.device == self.token.device,
                    Token.token.endswith(token_last_eight),
                )
                .get()
            )
        except Token.DoesNotExist:
            raise Http404()

    def get(self, request, token_last_eight):
        authorisation = self.get_authorisation(token_last_eight)
        return serialise_authorisation(authorisation)

    def delete(self, request, token_last_eight):
        authorisation = self.get_authorisation(token_last_eight)
        authorisation.delete_instance()
        return Response(status=204)
