import hashlib
import uuid
import os

import redis
from rq import Queue
import peewee

from rivr.router import Router
from rivr.http import Http404, Response, RESTResponse
from rivr.views import RESTView

from palaverapi.models import database, Device, Token
from palaverapi.utils import send_notification


router = Router()
app = router

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis = redis.from_url(redis_url)
queue = Queue(connection=redis)


@router.register(r'^$')
def status(request):
    return Response(status=204)

@router.register(r'^500$')
def crash(request):
    raise RuntimeError("You are eaten by a grue")


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


class PermissionRequiredMixin(object):
    scope_required = 'all'

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

    def has_permission(self):
        self.token = self.get_token()
        return self.token and (self.token.scope == 'all' or self.token.scope == self.scope_required)

    def handle_no_permission(self):
        return Response(status=401)

    def dispatch(self, request, *args, **kwargs):
        self.request = request

        if not self.has_permission():
            return self.handle_no_permission()

        return super(PermissionRequiredMixin, self).dispatch(request, *args, **kwargs)


class PushView(PermissionRequiredMixin, RESTView):
    scope_required = 'push'

    def post(self, request):
        try:
            attributes = request.POST
        except (UnicodeDecodeError, ValueError):
            return Response(status=400)

        message = attributes.get('message', None)
        sender = attributes.get('sender', None)
        channel = attributes.get('channel', None)
        network = attributes.get('network', None)
        badge = int(attributes.get('badge', 1))
        intent = attributes.get('intent', None)
        private = attributes.get('private', False)

        with database:
            token = self.get_token()
            if not token:
                return Response(status=401)

            queue.enqueue(send_notification, token.device.apns_token, message, sender, channel, badge, network, intent, private)

        return Response(status=202)


router.register(r'^1/push$', PushView.as_view())


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

    def post(self, request):
        try:
            attributes = request.POST
        except (UnicodeDecodeError, ValueError):
            return Response(status=400)

        scopes = attributes.get('scopes', None)
        scope = Token.ALL_SCOPE
        if scopes and len(scopes) == 1:
            if scopes[0] == Token.ALL_SCOPE or scopes[0] == Token.PUSH_SCOPE:
                scope = scopes[0]

        token = attributes.get('token', None)
        if token is None or not len(token) > 20:
            token = str(uuid.uuid4())

        authorisation = Token.create(device=self.token.device, token=token, scope=scope)
        attributes = serialise_authorisation(self.token)
        attributes['token'] = token
        return RESTResponse(request, attributes, status=201)


class AuthorisationDetailView(PermissionRequiredMixin, RESTView):
    def get_authorisation(self, token_last_eight):
        try:
            return Token.select().where(Token.device == self.token.device, Token.token.endswith(token_last_eight)).get()
        except Token.DoesNotExist:
            raise Http404()

    def get(self, request, token_last_eight):
        authorisation = self.get_authorisation(token_last_eight)
        return serialise_authorisation(authorisation)

    def delete(self, request, token_last_eight):
        authorisation = self.get_authorisation(token_last_eight)
        authorisation.delete_instance()
        return Response(status=204)


router.register(r'^authorisations$', AuthorisationListView.as_view())
router.register(r'^authorisations/(?P<token_last_eight>[\w]+)$', AuthorisationDetailView.as_view())
