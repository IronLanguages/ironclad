
def __new__(cls, *args, **kwargs):
    return cls._dispatcher.newfunc('{0}.tp_new', cls, args, kwargs)

def __del__(self):
    self._dispatcher.ic_destroy('{0}', self)

_ironclad_class_attrs['__new__'] = __new__
_ironclad_class_attrs['__del__'] = __del__

_ironclad_class = _ironclad_metaclass('{0}', _ironclad_bases, _ironclad_class_attrs)
_ironclad_class.__doc__ = '''{2}'''
_ironclad_class.__module__ = '{1}'
