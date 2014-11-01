from collections import namedtuple

__author__ = 'bernd'


class CommonEqualityMixin(object):
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)


MsgRecord = namedtuple('MsgRecord', 'path field msg'.split())
