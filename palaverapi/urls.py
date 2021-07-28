from rivr import Router
from rivr.middleware import ErrorWrapper

from palaverapi.models import database
from palaverapi.responses import ProblemResponse
from palaverapi.views import crash, handle_error, index, status
from palaverapi.views.authorisation import (
    AuthorisationDetailView,
    AuthorisationListView,
)
from palaverapi.views.device import DeviceDetailView, RegisterView
from palaverapi.views.push import PushView, PushViewRFC

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


app = ErrorWrapper(
    database(urls),
    custom_404=lambda request, e: ProblemResponse(404, 'Resource Not Found'),
    custom_500=handle_error,
)
