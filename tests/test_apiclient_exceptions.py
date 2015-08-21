import unittest

from freezer.apiclient import exceptions


class TestApiClientException(unittest.TestCase):

    def test_get_message_from_response_string(self):
        e = exceptions.ApiClientException('some error message')
        self.assertEquals(e.message, 'some error message')
