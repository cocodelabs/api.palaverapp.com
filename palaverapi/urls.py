from rivr import Router

from palaverapi.views import crash, index, status
from palaverapi.views.authorisation import (
    AuthorisationDetailView,
    AuthorisationListView,
)
from palaverapi.views.device import DeviceDetailView, RegisterView
from palaverapi.views.push import PushView, PushViewRFC

__all__ = ['urls']

urls = Router(
    (r'^$', index),
    (r'^health$', status),
    (r'^500$', crash),
    (r'^1/devices$', RegisterView.as_view()),
    (r'^1/push$', PushView.as_view()),
    (r'^push/(?P<subscription_id>[\w_-]+)$', PushViewRFC.as_view()),
    (r'^device$', DeviceDetailView.as_view()),
    (r'^authorisations$', AuthorisationListView.as_view()),
    (
        r'^authorisations/(?P<token_last_eight>[\w]+)$',
        AuthorisationDetailView.as_view(),
    ),
)
