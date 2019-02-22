import os
import thread
from invoke import run, task
from time import sleep


@task
def dropdb():
    from palaverapi.models import database, Device, Token
    Token.drop_table(True)
    Device.drop_table(True)

@task
def syncdb():
    from palaverapi.models import database, Device, Token
    Device.create_table()
    Token.create_table()

@task
def upload_certs():
    with open('certificates/private.pem') as fp:
        priv_key = fp.read()

    with open('certificates/public.pem') as fp:
        pub_key = fp.read()

    run('heroku config:add "APNS_PRIVATE_KEY={}" --app palaverapi'.format(priv_key))
    run('heroku config:add "APNS_PUBLIC_KEY={}" --app palaverapi'.format(pub_key))

def configure_db():
    database_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tests.sqlite')
    os.environ['DATABASE_URL'] = 'sqlite:///{}'.format(database_path)
    run('invoke dropdb')
    run('invoke syncdb')

@task
def tests():
    configure_db()
    run('python -m unittest discover')

@task
def test_blueprint():
    configure_db()

    from rivr import serve
    from palaverapi.views import router
    thread.start_new_thread(serve, (router,))

    run('dredd ./apiary.apib http://localhost:8080/')

@task
def cleanup():
    import sys
    import math
    from palaverapi.utils import load_apns_client, TOPIC
    from palaverapi.models import Device
    from apns2.errors import BadDeviceToken, Unregistered
    from apns2.payload import Payload

    apns_client = load_apns_client()

    payload = Payload() # No alert is shown to recipient if payload is empty.

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
            try:
                client.send_notification(device.apns_token, payload, TOPIC)
            except (BadDeviceToken, Unregistered) as e:
                device.delete_instance(recursive=True)
                removed_devices += 1

        sleep(10)


    print('\nDone! Removed {} devices.'.format(removed_devices))
