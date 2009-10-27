
def _ironclad_lt(self, other):
    return self._dispatcher.richcmpfunc('{0}tp_richcompare', self, other, 0)
def _ironclad_le(self, other):
    return self._dispatcher.richcmpfunc('{0}tp_richcompare', self, other, 1)
def _ironclad_eq(self, other):
    return self._dispatcher.richcmpfunc('{0}tp_richcompare', self, other, 2)
def _ironclad_ne(self, other):
    return self._dispatcher.richcmpfunc('{0}tp_richcompare', self, other, 3)
def _ironclad_gt(self, other):
    return self._dispatcher.richcmpfunc('{0}tp_richcompare', self, other, 4)
def _ironclad_ge(self, other):
    return self._dispatcher.richcmpfunc('{0}tp_richcompare', self, other, 5)

_ironclad_class_attrs['__lt__'] = _ironclad_lt
_ironclad_class_attrs['__le__'] = _ironclad_le
_ironclad_class_attrs['__eq__'] = _ironclad_eq
_ironclad_class_attrs['__ne__'] = _ironclad_ne
_ironclad_class_attrs['__gt__'] = _ironclad_gt
_ironclad_class_attrs['__ge__'] = _ironclad_ge
