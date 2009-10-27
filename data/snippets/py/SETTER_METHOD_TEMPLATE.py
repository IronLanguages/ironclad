
def _ironclad_setter(self, value):
    return self._dispatcher.ic_setter_method('{1}{0}', self, value, IntPtr({2}))
_ironclad_class_attrs['{0}'] = _ironclad_setter
