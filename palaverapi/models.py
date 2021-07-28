import os

import peewee
from rivr_peewee import Database

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgres+pool://')

    # disable auto connection
    EXTRA_OPTIONS = 'autoconnect=false'

    if '?' in DATABASE_URL:
        DATABASE_URL += '&' + EXTRA_OPTIONS
    else:
        DATABASE_URL += '?' + EXTRA_OPTIONS

    os.environ['DATABASE_URL'] = DATABASE_URL


database = Database()


class Device(database.Model):
    apns_token = peewee.CharField(max_length=64, unique=True)

    def __repr__(self) -> str:
        return '<Device {}>'.format(self.apns_token)


class Token(database.Model):
    PUSH_SCOPE = 'push'
    ALL_SCOPE = 'all'

    device = peewee.ForeignKeyField(Device)
    token = peewee.CharField(max_length=64, unique=True, primary_key=True)
    scope = peewee.CharField(max_length=10, choices=(PUSH_SCOPE, ALL_SCOPE))

    def __repr__(self) -> str:
        return '<Token {} ({})>'.format(self.token, self.scope)

    @property
    def token_last_eight(self) -> str:
        return self.token[-8:]
