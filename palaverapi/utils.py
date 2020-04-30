import os
from apns2.client import APNsClient
from apns2.errors import BadDeviceToken, Unregistered
from apns2.payload import Payload
from bugsnag import Client
from palaverapi.models import database, Device

TOPIC = 'com.kylefuller.palaver'
DIRECTORY = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certificates')
)
bugsnag_client = Client(asynchronous=False, install_sys_hook=False)
apns_client = None


def load_apns_client():
    global apns_client

    if apns_client is None:
        apns_client = APNsClient(
            os.path.join(DIRECTORY, 'production.pem'), heartbeat_period=30
        )

    return apns_client


@bugsnag_client.capture()
def send_notification(
    apns_token,
    message,
    sender,
    channel,
    badge=1,
    network=None,
    intent=None,
    private=False,
):
    apns_client = load_apns_client()

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
    thread_id = None

    if query and network:
        user_info['n'] = network
        user_info['q'] = query
        thread_id = 'plv://{0}/{1}'.format(network, query)

    if sender:
        alert['title'] = sender

    if channel:
        alert['subtitle'] = channel

    if private:
        alert['loc-key'] = 'INPUT_MESSAGE_PLACEHOLDER'
        alert['body'] = 'Message'
    elif message:
        alert['body'] = message

    payload = Payload(alert=alert, sound=sound, badge=badge, custom=user_info, thread_id=thread_id)

    apns_client.connect()

    try:
        apns_client.send_notification(apns_token, payload, TOPIC)
    except (BadDeviceToken, Unregistered) as e:
        with database.transaction():
            try:
                device = Device.get(Device.apns_token == apns_token)
                device.delete_instance(recursive=True)
            except Device.DoesNotExist:
                return
