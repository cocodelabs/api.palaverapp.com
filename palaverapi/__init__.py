import os
import logging

from rivr.wsgi import WSGIHandler

from palaverapi.views import app

logger = logging.getLogger('rivr.request')

if os.environ.get('BUGSNAG_API_KEY'):
    from bugsnag.handlers import BugsnagHandler
    handler = BugsnagHandler()
    handler.setLevel(logging.ERROR)
    logger.addHandler(handler)
else:
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    logger.addHandler(console)


wsgi = WSGIHandler(app)
