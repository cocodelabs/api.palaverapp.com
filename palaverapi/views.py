import hashlib

from rivr.router import Router
from rivr.http import Response, RESTResponse
from rivr.views import RESTView

from palaverapi.models import database, Device, Token
from palaverapi.utils import send_notification


router = Router()

@router.register(r'^$')
def status(request):
    return Response(status=204)


class RegisterView(RESTView):
    def post(self, request):
        apns_token = request.POST['device_token']
        push_token = hashlib.sha1(hashlib.sha1(apns_token + apns_token).hexdigest()).hexdigest()

        with database.transaction():
            device = Device.create(apns_token=apns_token)
            token = Token.create(device=device, token=apns_token, scope=Token.ALL_SCOPE)
            push = Token.create(device=device, token=push_token, scope=Token.PUSH_SCOPE)

        return RESTResponse(request, {
            'device_token': apns_token,
            'push_token': push_token,
        }, status=201)


router.register(r'^1/devices$', RegisterView.as_view())


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
        token = self.get_token()
        if not token:
            return Response(status=401)

        message = request.POST.get('message', None)
        sender = request.POST.get('sender', None)
        channel = request.POST.get('channel', None)
        network = request.POST.get('network', None)
        badge = int(request.POST.get('badge', 1))
        success = send_notification(token.device.apns_token, message, sender, channel, badge, network)

router.register(r'^1/push$', PushView.as_view())

