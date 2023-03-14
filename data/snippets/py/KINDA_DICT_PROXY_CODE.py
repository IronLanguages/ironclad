
from collections import UserDict

class KindaDictProxy(UserDict):
    def __init__(self, initialdata):
        super().__init__()
        self.data.update(initialdata)
    
    def __setitem__(self, key, value):
        raise TypeError('read-only dict')
    
    def __delitem__(self, key):
        raise TypeError('read-only dict')
