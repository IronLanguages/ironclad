
def __new__(cls, *args, **kwargs):
    if issubclass(cls, int):
        raise NotImplementedError # https://github.com/IronLanguages/ironclad/issues/14
    if issubclass(cls, float):
        return float.__new__(cls, args[0])
    if issubclass(cls, str):
        raise NotImplementedError # https://github.com/IronLanguages/ironclad/issues/13
    if issubclass(cls, bytes):
        return bytes.__new__(cls, args[0])
    if issubclass(cls, type):
        return type.__new__(cls, *args, **kwargs)
    return object.__new__(cls)

def __init__(self, *args, **kwargs):
    pass

def __del__(self):
    pass

def __setattr__(self, name, value):
    # not directly tested: if you can work out how to, be my guest
    # numpy fromrecords test will overflow stack if this breaks
    if isinstance(self, type):
        type.__setattr__(self, name, value)
    else:
        object.__setattr__(self, name, value)

_ironclad_class_stub = _ironclad_metaclass('_ironclad_class_stub', _ironclad_bases, {
    '__new__': __new__,
    '__init__': __init__,
    '__del__': __del__,
    '__setattr__': __setattr__,
})
