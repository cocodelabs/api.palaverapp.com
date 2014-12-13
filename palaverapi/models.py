import peewee
import pw_database_url


def load_database():
    config = pw_database_url.config()
    name = config.pop('name')
    _, engine = config.pop('engine').split('.', 2)
    config = dict((k, v) for k, v in config.items() if v)
    return getattr(peewee, engine)(name, **config)

database = load_database()


class Model(peewee.Model):
    class Meta:
        database = database


class Device(Model):
    apns_token = peewee.CharField(max_length=64, unique=True)

    def __repr__(self):
        return '<Device {}>'.format(self.apns_token)


class Token(Model):
    PUSH_SCOPE = 'push'
    ALL_SCOPE = 'all'

    device = peewee.ForeignKeyField(Device)
    token = peewee.CharField(max_length=64, unique=True, primary_key=True)
    scope = peewee.CharField(max_length=10, choices=(PUSH_SCOPE, ALL_SCOPE))

    def __repr__(self):
        return '<Token {} ({})>'.format(self.token, self.scope)

