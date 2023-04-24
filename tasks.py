import os
import asyncio
from threading import Thread
from invoke import run, task
from time import sleep


@task
def dropdb(context):
    from palaverapi.models import database, Device, Token

    Token.drop_table(True)
    Device.drop_table(True)


@task
def syncdb(context):
    from palaverapi.models import database, Device, Token

    Device.create_table()
    Token.create_table()


def configure_db():
    database_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 'tests.sqlite'
    )
    os.environ['DATABASE_URL'] = 'sqlite:///{}'.format(database_path)
    run('invoke dropdb')
    run('invoke syncdb')


@task
def tests(context):
    configure_db()
    run('pytest')


@task
def test_blueprint(context):
    configure_db()

    from rivr import serve
    from palaverapi.views import router

    thread = Thread(target=serve, args=(router,))
    thread.start()

    run('dredd ./apiary.apib http://localhost:8080/')


@task
def cleanup(context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_cleanup(context))

async def _cleanup(context):
    import sys
    import math
    from palaverapi.utils import load_apns_client, TOPIC
    from palaverapi.models import Device
    from aioapns import NotificationRequest, PushType, PRIORITY_NORMAL
    from aioapns.common import APNS_RESPONSE_CODE

    apns_client = load_apns_client()

    stepsize = 500
    total = Device.select().count()
    steps = int(math.ceil(float(total) / float(stepsize)))
    removed_devices = 0

    print('Currently {} devices in database.'.format(total))

    for i in range(0, steps):
        # Print progress percentage
        frac = float(i * stepsize) / float(total)
        sys.stdout.write('\r{:>6.1%}'.format(frac))
        sys.stdout.flush()

        devices = Device.select().limit(stepsize).offset(i * stepsize).execute()

        for device in devices:
            request = NotificationRequest(
                device_token=device.apns_token,
                message={ 'aps': {} },
                push_type=PushType.BACKGROUND,  # No alert is shown to recipient if push type is background
                priority=PRIORITY_NORMAL
            )
            response = await apns_client.send_notification(request)
            if response.description in ['BadDeviceToken', 'Unregistered']:
                device.delete_instance(recursive=True)
                removed_devices += 1
            elif not response.is_successful:
                raise Exception('Unsuccesful APNS request', response.description)

        sleep(10)

    print('\nDone! Removed {} devices.'.format(removed_devices))
