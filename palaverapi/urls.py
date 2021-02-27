from rivr import Router
from rivr.middleware import ErrorWrapper

from palaverapi.models import database
from palaverapi.responses import ProblemResponse
from palaverapi.views import (
    AuthorisationDetailView,
    AuthorisationListView,
    DeviceDetailView,
    PushView,
    RegisterView,
    crash,
    handle_error,
    index,
    status,
)

urls = Router(
    (r'^$', index),
    (r'^health$', status),
    (r'^500$', crash),
    (r'^1/devices$', database(RegisterView.as_view())),
    (r'^1/push$', PushView.as_view()),
    (r'^device$', DeviceDetailView.as_view()),
    (r'^authorisations$', AuthorisationListView.as_view()),
    (
        r'^authorisations/(?P<token_last_eight>[\w]+)$',
        AuthorisationDetailView.as_view(),
    ),
)


app = ErrorWrapper(
    urls,
    custom_404=lambda request, e: ProblemResponse(404, 'Resource Not Found'),
    custom_500=handle_error,
)
