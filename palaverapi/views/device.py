import hashlib

import peewee
from rivr.http import Response
from rivr.views import View

from palaverapi.decorators import requires_body
from palaverapi.models import Device, Token, database
from palaverapi.responses import RESTResponse
from palaverapi.views.mixins import PermissionRequiredMixin


class RegisterView(View):
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


class DeviceDetailView(PermissionRequiredMixin, View):
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
