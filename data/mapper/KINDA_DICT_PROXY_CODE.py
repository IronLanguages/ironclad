
from UserDict import IterableUserDict

class KindaDictProxy(IterableUserDict):
    
    def __setitem__(self, key, value):
        raise TypeError('read-only dict')
    
    def __delitem__(self, key):
        raise TypeError('read-only dict')
        
