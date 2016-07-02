import os
from apns import APNs, Payload, MAX_PAYLOAD_LENGTH


DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certificates'))

def send_notification(apns_token, message, sender, channel, badge=1, network=None, intent=None):
    apns = APNs(cert_file=os.path.join(DIRECTORY, 'public.pem'),
                key_file=os.path.join(DIRECTORY, 'private.pem'))

    query = None

    if sender and message:
        if intent == 'ACTION':
            message = '* %s %s' % (sender, message)
        else:
            message = '<%s> %s' % (sender, message)

        query = sender

    if channel and message:
        message = '%s %s' % (channel, message)
        query = channel

    sound = None
    alert = None

    if message:
        sound = 'default'
        alert = '.'

    user_info = {}

    if query and network:
        user_info['n'] = network
        user_info['q'] = query

    payload = Payload(alert=alert, sound=sound, badge=badge, custom=user_info)
    if message:
        payload_length = len(payload.json())
        if (payload_length + len(message) - 1) >= MAX_PAYLOAD_LENGTH:
            message = message[:(MAX_PAYLOAD_LENGTH - payload_length - 3)] + '...'
        payload.alert = message

    apns.gateway_server.send_notification(apns_token, payload)

    success = True

    for (token_hex, fail_time) in apns.feedback_server.items():
        if apns_token == token_hex:
            success = False
        else:
            pass

    return success

