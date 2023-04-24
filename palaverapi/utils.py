import os
from typing import Optional

from aioapns import APNs, NotificationRequest, PushType, PRIORITY_HIGH
from aioapns.common import APNS_RESPONSE_CODE
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


def load_apns_client() -> APNs:
    global apns_client
    if apns_client is None:
        auth_key_path = os.path.join(KEYS_DIRECTORY, f'{AUTH_KEY_ID}.pem')
        apns_client = APNs(
            key_id=AUTH_KEY_ID,
            key=auth_key_path,
            team_id=TEAM_ID,
            topic=TOPIC,
            use_sandbox=False,
        )

    return apns_client


def create_payload(
    message,
    sender,
    channel,
    badge=1,
    network=None,
    intent=None,
    private=False,
) -> dict:
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

    return {
        'alert': alert,
        'sound': sound,
        'badge': badge,
        'thread_id': thread_id,
        **user_info
    }


async def send_payload(
    apns_token: str, payload: dict, priority: Optional[str] = None
) -> None:
    apns_client = load_apns_client()

    request = NotificationRequest(
        device_token=apns_token,
        message={ 'aps': payload },
        push_type=PushType.ALERT,
        priority=priority or PRIORITY_HIGH
    )
    response = await apns_client.send_notification(request)
    if response.description in ['BadDeviceToken', 'Unregistered']:
        with database.transaction():
            try:
                device = Device.get(Device.apns_token == apns_token)
                device.delete_instance(recursive=True)
            except Device.DoesNotExist:
                return
    elif not response.is_successful:
        raise Exception('Unsuccesful APNS request', response.description)


@bugsnag_client.capture()
async def send_notification(
    apns_token: str, *args, priority: Optional[str] = None, **kwargs
) -> None:
    payload = create_payload(*args, **kwargs)
    await send_payload(apns_token, payload, priority=priority)
