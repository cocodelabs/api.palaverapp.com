import os
from apns2.client import APNsClient
from apns2.payload import Payload
from bugsnag import Client

TOPIC = 'com.kylefuller.palaver'
DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certificates'))
bugsnag_client = Client(asynchronous=False, install_sys_hook=False)
apns_client = None

@bugsnag_client.capture()
def send_notification(apns_token, message, sender, channel, badge=1, network=None, intent=None, private=False):
    global apns_client

    if apns_client is None:
        apns_client = APNsClient(os.path.join(DIRECTORY, 'production.pem'), heartbeat_period=30)

    query = None

    if channel:
        query = channel
    elif sender:
        query = sender

    if message and intent == 'ACTION':
        message = '* %s' % (message)

    sound = None
    alert = {}

    if message or private:
        sound = 'default'

    user_info = {}

    if query and network:
        user_info['n'] = network
        user_info['q'] = query

    if sender:
        alert['title'] = sender

    if channel:
        alert['subtitle'] = channel

    if private:
        alert['loc-key'] = 'INPUT_MESSAGE_PLACEHOLDER'
        alert['body'] = 'Message'
    elif message:
        alert['body'] = message

    payload = Payload(alert=alert, sound=sound, badge=badge, custom=user_info)

    apns_client.connect()
    apns_client.send_notification(apns_token, payload, TOPIC)
