import logging
import os

from rivr.middleware import ErrorWrapper, MiddlewareController
from rivr.wsgi import WSGIHandler

from palaverapi.models import database
from palaverapi.urls import urls
from palaverapi.views import handle_error, handle_not_found

middleware = MiddlewareController.wrap(urls, database)

app = ErrorWrapper(
    middleware,
    custom_404=handle_not_found,
    custom_500=handle_error,
)

logger = logging.getLogger('rivr.request')
if os.environ.get('BUGSNAG_API_KEY'):
    from bugsnag import Client

    client = Client()
    handler = client.log_handler()
    handler.setLevel(logging.ERROR)
    logger.addHandler(handler)
else:
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    logger.addHandler(console)

wsgi = WSGIHandler(app)
