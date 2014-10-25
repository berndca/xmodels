from .utility import ParseError
from .datetimestamps import parse_date, parse_time
from .timezones import Timezone

__all__ = ['parse',
           'parse_date',
           'parse_time',
           'Timezone',
           'ParseError']


def parse(representation):
    """Attempts to parse an ISO8601 formatted ``representation`` string,
    which could be of any valid ISO8601 format (date, time, duration,
    interval).

    Return value is specific to ``representation``.
    """
    representation = str(representation).upper().strip()
    return parse_date(representation)
