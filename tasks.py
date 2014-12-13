import os
import thread
from invoke import run, task


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

