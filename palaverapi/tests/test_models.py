import unittest
from peewee import IntegrityError
from palaverapi.models import database, Device, Token


class DeviceTests(unittest.TestCase):
    def setUp(self):
        super(DeviceTests, self).setUp()
        apns_token = 'test_apns_token'
        self.device = Device.create(apns_token=apns_token)

    def tearDown(self):
        super(DeviceTests, self).tearDown()
        self.device.delete_instance()

    def testDeviceHasAPNSToken(self):
        self.assertEqual(self.device.apns_token, 'test_apns_token')

    def testEnsureDeviceUniqueByAPNSToken(self):
        with database.transaction():
            self.assertRaises(IntegrityError, Device.create,
                    apns_token=self.device.apns_token)


class TokenTests(unittest.TestCase):
    def setUp(self):
        super(TokenTests, self).setUp()
        apns_token = 'test_apns_token'
        self.device = Device.create(apns_token=apns_token)

        token = 'test_token'
        self.token = Token.create(device=self.device, token=token, scope=Token.PUSH_SCOPE)

    def tearDown(self):
        super(TokenTests, self).tearDown()
        self.token.delete_instance()
        self.device.delete_instance()

    def testTokenHasPushScope(self):
        self.assertEqual(Token.PUSH_SCOPE, 'push')

    def testTokenHasAllScope(self):
        self.assertEqual(Token.ALL_SCOPE, 'all')

    def testTokenHasToken(self):
        self.assertEqual(self.token.token, 'test_token')

    def testTokenHasDevice(self):
        self.assertEqual(self.token.device, self.device)

    def testTokenHasScope(self):
        self.assertEqual(self.token.scope, 'push')

    def testEnsureTokenUniqueByAPNSToken(self):
        with database.transaction():
            self.assertRaises(IntegrityError, Token.create,
                    device=self.device, token=self.token.token,
                    scope=Token.ALL_SCOPE)

    def test_delete_device(self):
        self.device.delete_instance(recursive=True)
        self.assertFalse(Token.select().exists())
        self.assertFalse(Device.select().exists())
