import os
import logging
from logging.handlers import SMTPHandler

from rivr.wsgi import WSGIHandler
from palaverapi.views import app

logger = logging.getLogger('rivr.request')

if os.environ.get('SENDGRID_USERNAME'):
    mail_handler = SMTPHandler('smtp.sendgrid.net',
                               'support@palaverapp.com',
                               ['support@palaverapp.com'],
                               '[API Error] Heroku',
                               credentials=(os.environ['SENDGRID_USERNAME'],
                                            os.environ['SENDGRID_PASSWORD']))
    mail_handler.setLevel(logging.ERROR)
    logger.addHandler(mail_handler)
    mail_handler.setFormatter(logging.Formatter("""\
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:

%(message)s"""))
else:
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    logger.addHandler(console)


wsgi = WSGIHandler(app)

