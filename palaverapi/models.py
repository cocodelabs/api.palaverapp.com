from rivr_peewee import Database
import peewee


database = Database()


class Device(database.Model):
    apns_token = peewee.CharField(max_length=64, unique=True)

    def __repr__(self):
        return '<Device {}>'.format(self.apns_token)


class Token(database.Model):
    PUSH_SCOPE = 'push'
    ALL_SCOPE = 'all'

    device = peewee.ForeignKeyField(Device)
    token = peewee.CharField(max_length=64, unique=True, primary_key=True)
    scope = peewee.CharField(max_length=10, choices=(PUSH_SCOPE, ALL_SCOPE))

    def __repr__(self):
        return '<Token {} ({})>'.format(self.token, self.scope)

    @property
    def token_last_eight(self):
        return self.token[-8:]
