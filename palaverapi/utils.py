import os
from apns import APNs, Payload, MAX_PAYLOAD_LENGTH
from bugsnag import Client

DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certificates'))
client = Client(asynchronous=False, install_sys_hook=False)

@client.capture
def send_notification(apns_token, message, sender, channel, badge=1, network=None, intent=None, private=False):
    apns = APNs(cert_file=os.path.join(DIRECTORY, 'public.pem'),
                key_file=os.path.join(DIRECTORY, 'private.pem'))

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

    apns.gateway_server.send_notification(apns_token, payload)

    success = True

    for (token_hex, fail_time) in apns.feedback_server.items():
        if apns_token == token_hex:
            success = False
        else:
            pass

    return success

