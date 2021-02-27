from typing import Optional

from rivr.http import Request, Response

from palaverapi.models import Token
from palaverapi.responses import ProblemResponse


class PermissionRequiredMixin(object):
    scope_required = 'all'

    def get_token(self) -> Optional[Token]:
        authorization = self.request.headers.get('AUTHORIZATION', None)
        if not authorization or (authorization and ' ' not in authorization):
            return None

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

    def handle_no_permission(self) -> Response:
        return ProblemResponse(401, 'Unauthorized')

    def dispatch(self, request: Request, *args, **kwargs) -> Response:
        self.request = request

        if not self.has_permission():
            return self.handle_no_permission()

        return super(PermissionRequiredMixin, self).dispatch(request, *args, **kwargs)
