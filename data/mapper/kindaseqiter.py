
from itertools import count

class KindaSeqIter(object):
    def __init__(self, obj):
        if isinstance(obj, type) or not hasattr(obj, '__getitem__'):
            raise TypeError()
        self.obj = obj
        self.index = -1
    def __iter__(self):
        return self
    def next(self):
        self.index += 1
        try:
            return self.obj[self.index]
        except IndexError:
            raise StopIteration()