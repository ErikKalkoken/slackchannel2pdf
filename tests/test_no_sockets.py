import urllib.request

from .helpers.no_sockets import NoSocketsTestCase, SocketAccessError


class TestNoSocketsTestCase(NoSocketsTestCase):
    def test_raises_exception_on_attempted_network_access(self):

        with self.assertRaises(SocketAccessError):
            urllib.request.urlopen("https://www.google.com")
