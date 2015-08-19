import unittest
from freezer.osclients import ClientManager
from freezer.utils import OpenstackOptions


class TestOsClients(unittest.TestCase):

    fake_options = OpenstackOptions(user_name="user", tenant_name="tenant",
                                    project_name="project", auth_url="url",
                                    password="password",
                                    identity_api_version="3"
                                    )

    def test_init(self):
        ClientManager(self.fake_options, None, None, None)

    def test_create_cinder(self):
        client = ClientManager(self.fake_options, None, None, None)
        client.create_cinder()

    def test_create_swift(self):
        client = ClientManager(self.fake_options, None, None, None)
        client.create_swift()

    def test_create_nova(self):
        client = ClientManager(self.fake_options, None, None, None)
        client.create_nova()

    def test_create_swift_public(self):
        options = OpenstackOptions(user_name="user", tenant_name="tenant",
                                   project_name="project", auth_url="url",
                                   password="password",
                                   identity_api_version="3",
                                   endpoint_type="adminURL")
        client = ClientManager(options, None, None, None)
        client.create_swift()