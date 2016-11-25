class TimeoutException(Exception):
    msg = "Timeout has been occured."

    def __init__(self, message=None, **kwargs):
        if not message:
            message = self.msg
        super(TimeoutException, self).__init__(message, kwargs)
