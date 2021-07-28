import os
from typing import Optional

from apns2.client import APNsClient, NotificationPriority
from apns2.credentials import TokenCredentials
from apns2.errors import BadDeviceToken, Unregistered
from apns2.payload import Payload
from bugsnag import Client

from palaverapi.models import Device, database

TOPIC = 'com.kylefuller.palaver'
KEYS_DIRECTORY = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'keys')
)
AUTH_KEY_ID = os.environ.get('APNS_AUTH_KEY_ID')
TEAM_ID = os.environ.get('APNS_TEAM_ID')
bugsnag_client = Client(asynchronous=False, install_sys_hook=False)
apns_client = None


def load_apns_client() -> APNsClient:
    global apns_client
    if apns_client is None:
        auth_key_path = os.path.join(KEYS_DIRECTORY, f'{AUTH_KEY_ID}.pem')
        token_credentials = TokenCredentials(
            auth_key_path=auth_key_path, auth_key_id=AUTH_KEY_ID, team_id=TEAM_ID
        )
        apns_client = APNsClient(credentials=token_credentials, heartbeat_period=30)

    return apns_client


def create_payload(
    message,
    sender,
    channel,
    badge=1,
    network=None,
    intent=None,
    private=False,
) -> Payload:
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

    return Payload(
        alert=alert, sound=sound, badge=badge, custom=user_info, thread_id=thread_id
    )


def send_payload(
    apns_token: str, payload: Payload, priority: Optional[NotificationPriority] = None
) -> None:
    apns_client = load_apns_client()
    apns_client.connect()

    try:
        apns_client.send_notification(
            apns_token,
            payload,
            TOPIC,
            priority=priority or NotificationPriority.Immediate,
        )
    except (BadDeviceToken, Unregistered):
        with database.transaction():
            try:
                device = Device.get(Device.apns_token == apns_token)
                device.delete_instance(recursive=True)
            except Device.DoesNotExist:
                return


@bugsnag_client.capture()
def send_notification(
    apns_token: str, *args, priority: Optional[NotificationPriority] = None, **kwargs
) -> None:
    payload = create_payload(*args, **kwargs)
    send_payload(apns_token, payload, priority=priority)
