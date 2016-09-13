import os
import logging

from rivr.wsgi import WSGIHandler

from palaverapi.views import app

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
