from freezer.bandwidth import ThrottledSocket, monkeypatch_bandwidth
from commons import FakeSocket


class TestBandwidth:

    def test_throttled_socket_recv(self):
        fake = FakeSocket()
        throttled = ThrottledSocket(100, 100, fake)
        assert throttled.recv() == fake.recv()

    def test_throttled_socket_send(self):
        fake = FakeSocket()
        throttled = ThrottledSocket(100, 100, fake)
        with pytest.raises(Exception) as excinfo:
            throttled.sendall()
        assert "fake send" in excinfo.value

    def test_sleep_duration(self):
        assert ThrottledSocket._sleep_duration(10, 5, 5, 6) == 1.0
        assert ThrottledSocket._sleep_duration(10, 5, 5, 5.5) == 1.5
        assert ThrottledSocket._sleep_duration(10, 5, 5, 6.5) == 0.5
        assert ThrottledSocket._sleep_duration(10, 5, 5, 7) == 0.0

    def test_sleep(self):
        ThrottledSocket._sleep(10, 5, 5, 7)

    def test_monkeypatch(self):
        monkeypatch_bandwidth(100, 100)

    def test_set(self):
        fake = FakeSocket()
        ThrottledSocket(100, 100, fake).__setattr__("test", 12)
        ThrottledSocket(100, 100, fake).__getattr__("test")
