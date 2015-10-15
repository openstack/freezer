import socket
import time


class ThrottledSocket(object):
    def __init__(self, download_limit, upload_limit, wrappedsock):
        self.__dict__['_wrappedsock'] = wrappedsock
        self.__dict__['download_limit'] = download_limit
        self.__dict__['upload_limit'] = upload_limit

    def __getattr__(self, attr):
        return getattr(self._wrappedsock, attr)

    def __setattr__(self, attr, value):
        return setattr(self._wrappedsock, attr, value)

    def recv(self, *args):
        start = time.time()
        buf = self._wrappedsock.recv(*args)
        self._sleep(len(buf), self.download_limit, start, time.time())
        return buf

    def sendall(self, *args):
        start = time.time()
        res = self._wrappedsock.send(*args)
        self._sleep(res, self.upload_limit, start, time.time())

    @staticmethod
    def _sleep_duration(transmitted, limit, start_time, end_time):
        exp_duration = float(transmitted) / limit
        expected_end = start_time + exp_duration
        return expected_end - end_time

    @staticmethod
    def _sleep(transmitted, limit, start_time, end_time):
        if limit > 1:
            sleep_duration = ThrottledSocket._sleep_duration(
                transmitted,
                limit,
                start_time,
                end_time)
            if sleep_duration > 0:
                time.sleep(sleep_duration)

    def makefile(self, mode='r', bufsize=-1):
        return socket._fileobject(self, mode, bufsize)


def monkeypatch_bandwidth(download_bytes_per_sec, upload_bytes_per_sec):
    """
        Monkey patch socket to ensure that all
        new sockets created are throttled.
    """
    if upload_bytes_per_sec > -1 or download_bytes_per_sec > - 1:
        def make_throttled_socket(*args, **kwargs):
            return ThrottledSocket(
                download_bytes_per_sec,
                upload_bytes_per_sec,
                socket._realsocket(*args, **kwargs))

        socket.socket = make_throttled_socket
        socket.SocketType = ThrottledSocket


def monkeypatch_socket_bandwidth(backup_opt_dict):
    download_limit = backup_opt_dict.download_limit
    upload_limit = backup_opt_dict.upload_limit
    monkeypatch_bandwidth(download_limit, upload_limit)
