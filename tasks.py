import os
from invoke import run, task
from palaverapi.models import database, Device, Token


@task
def dropdb():
    Token.drop_table(True)
    Device.drop_table(True)

@task
def syncdb():
    Device.create_table()
    Token.create_table()

@task
def tests():
    database_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'tests.sqlite')
    os.environ['DATABASE_URL'] = 'sqlite:///{}'.format(database_path)

    run('invoke dropdb')
    run('invoke syncdb')
    run('python -m unittest discover')

