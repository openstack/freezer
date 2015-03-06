import datetime
from django.template.defaultfilters import date as django_date


def timestamp_to_string(ts):
    return django_date(
        datetime.datetime.fromtimestamp(int(ts)),
        'SHORT_DATETIME_FORMAT')
