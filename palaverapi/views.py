import hashlib

from rivr.router import Router
from rivr.http import Response, RESTResponse
from rivr.views import RESTView

from palaverapi.models import database, Device, Token


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

