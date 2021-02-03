import socket
from unittest import TestCase


class SocketAccessError(Exception):
    pass


class NoSocketsTestCase(TestCase):
    """Enhancement of TestCase class that prevents any use of sockets

    Will throw the exception SocketAccessError when any code tries to
    access network sockets
    """

    @classmethod
    def setUpClass(cls):
        cls.socket_original = socket.socket
        socket.socket = cls.guard
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        socket.socket = cls.socket_original
        return super().tearDownClass()

    @staticmethod
    def guard(*args, **kwargs):
        raise SocketAccessError("Attempted to access network")
