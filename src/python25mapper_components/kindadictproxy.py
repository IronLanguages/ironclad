
from UserDict import UserDict

class KindaDictProxy(UserDict):
    
    def __setitem__(self, key, value):
        raise TypeError('read-only dict')
    
    def __delitem__(self, key):
        raise TypeError('read-only dict')
        
