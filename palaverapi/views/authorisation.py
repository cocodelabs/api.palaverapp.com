from typing import Any, Dict
import uuid

import peewee
from rivr.http import Http404, Request, Response
from rivr.views import View

from palaverapi.decorators import requires_body
from palaverapi.models import Token, database
from palaverapi.responses import ProblemResponse, RESTResponse
from palaverapi.views.mixins import PermissionRequiredMixin


def serialise_authorisation(token: Token) -> Dict[str, Any]:
    return {
        'url': '/authorisations/{}'.format(token.token_last_eight),
        'token_last_eight': token.token_last_eight,
        'scopes': [token.scope],
    }


class AuthorisationListView(PermissionRequiredMixin, View):
    def get(self, request: Request) -> Response:
        tokens = Token.select().where(Token.device == self.token.device)
        return RESTResponse(
            request, [serialise_authorisation(token) for token in tokens]
        )

    @requires_body
    def post(self, request: Request, attributes) -> Response:
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


class AuthorisationDetailView(PermissionRequiredMixin, View):
    def get_authorisation(self, token_last_eight: str) -> Token:
        try:
            token = (
                Token.select()
                .where(
                    Token.device == self.token.device,
                    Token.token.endswith(token_last_eight),
                )
                .get()
            )
        except Token.DoesNotExist:
            raise Http404()

        return token

    def get(self, request: Request, token_last_eight: str) -> Response:
        authorisation = self.get_authorisation(token_last_eight)
        return RESTResponse(request, serialise_authorisation(authorisation))

    def delete(self, request: Request, token_last_eight: str) -> Response:
        authorisation = self.get_authorisation(token_last_eight)
        authorisation.delete_instance()
        return Response(status=204)
