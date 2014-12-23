import os
import logging
from logging.handlers import SMTPHandler

from rivr.wsgi import WSGIHandler
from palaverapi.views import app


if os.environ.get('SENDGRID_USERNAME'):
    logger = logging.getLogger('rivr.request')
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


wsgi = WSGIHandler(app)

