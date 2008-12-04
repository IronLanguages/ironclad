
from UserDict import UserDict

class KindaDictProxy(UserDict):
    
    def __init__(self, proxied):
        self._proxied = proxied
    
    def __getitem__(self, key):
        return self._proxied[key]
    
    def __setitem__(self, key, value):
        raise TypeError('read-only dict')
    
    def __delitem__(self, key):
        raise TypeError('read-only dict')
        
