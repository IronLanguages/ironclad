namespace Ironclad
{
    internal partial class CodeSnippets
    {
        public const string NEW_EXCEPTION = @"
class {0}(Exception):
    __module__ = '{1}'
";

        public const string ACTUALISER_CODE = @"
class _ironclad_actualiser(_ironclad_class):
    def __new__(cls, *args, **kwargs):
        if issubclass(cls, int):
            return int.__new__(cls, args[0])
        return object.__new__(cls)
    def __init__(self, *args, **kwargs):
        pass
    def __del__(self):
        pass
    def __setattr__(self, name, value):
        # not directly tested: if you can work out how to, be my guest
        # numpy fromrecords test will overflow stack if this breaks
        object.__setattr__(self, name, value)
";

        public const string CLASS_CODE = @"
def __new__(cls, *args, **kwargs):
    return cls._dispatcher.construct('{0}.tp_new', cls, *args, **kwargs)
    
def __init__(self, *args, **kwargs):
    self._dispatcher.init('{0}.tp_init', self, *args, **kwargs)

def __del__(self):
    self._dispatcher.delete(self)

_ironclad_class_attrs['__new__'] = __new__
_ironclad_class_attrs['__init__'] = __init__
_ironclad_class_attrs['__del__'] = __del__

_ironclad_class = {0} = _ironclad_metaclass('{0}', _ironclad_bases, _ironclad_class_attrs)
{0}.__doc__ = '''{2}'''
{0}.__module__ = '{1}'

";
 
        public const string CLEAR_GETTER_SETTER_CODE = @"
_ironclad_getter = _ironclad_setter = None
";

        public const string MEMBER_GETTER_CODE = @"
def _ironclad_getter(self):
    return self._dispatcher.get_member_{2}(self, {1})

_ironclad_class_attrs['{0}'] = _ironclad_getter
";

        public const string MEMBER_SETTER_CODE = @"
def _ironclad_setter(self, value):
    self._dispatcher.set_member_{2}(self, {1}, value)

_ironclad_class_attrs['{0}'] = _ironclad_setter
";

        public const string GETTER_METHOD_CODE = @"
def _ironclad_getter(self):
    return self._dispatcher.method_getter('{1}{0}', self, IntPtr({2}))

_ironclad_class_attrs['{0}'] = _ironclad_getter
";

        public const string SETTER_METHOD_CODE = @"
def _ironclad_setter(self, value):
    return self._dispatcher.method_setter('{1}{0}', self, value, IntPtr({2}))

_ironclad_class_attrs['{0}'] = _ironclad_setter
";

        public const string PROPERTY_CODE = @"
_ironclad_class_attrs['{0}'] = property(_ironclad_getter, _ironclad_setter, None, '''{1}''')
";

	public const string GETATTR_CODE = @"
def _getattr(self, attr):
    return self._dispatcher.method_getattr('{2}{0}', self, attr)

_ironclad_class_attrs['{0}'] = _getattr
";

        public const string GETITEM_CODE = @"
def __getitem__(self, key):
    if isinstance(key, int) and hasattr(self, '_getitem_sq_item'):
        return self._getitem_sq_item(key)
    if hasattr(self, '_getitem_mp_subscript'):
        return self._getitem_mp_subscript(key)
    raise IndexError('no idea how to index %s' % key)

_ironclad_class_attrs['__getitem__'] = __getitem__
";

        public const string SETITEM_CODE = @"
def __setitem__(self, key, item):
    if isinstance(key, int) and hasattr(self, '_setitem_sq_ass_item'):
        return self._setitem_sq_ass_item(key, item)
    if hasattr(self, '_setitem_mp_ass_subscript'):
        return self._setitem_mp_ass_subscript(key, item)
    raise IndexError('no idea how to index %s' % key)

_ironclad_class_attrs['__setitem__'] = __setitem__
";

        public const string LEN_CODE = @"
def __len__(self):
    if hasattr(self, '_len_sq_length'):
        return self._len_sq_length()
    if hasattr(self, '_len_mp_length'):
        return self._len_mp_length()
    raise Exception('no idea how to len() this')

_ironclad_class_attrs['__len__'] = __len__
";

        public const string COMPLEX_HACK_CODE = @"
def __complex__(self):
    return complex(float(self.real), float(self.imag))
_ironclad_class_attrs['__complex__'] = __complex__
";

        public const string ITER_METHOD_CODE = @"
def __iter__(self):
    return self._dispatcher.method_selfarg('{0}tp_iter', self)
_ironclad_class_attrs['__iter__'] = __iter__
";

        public const string ITERNEXT_METHOD_CODE = @"
def __raise_stop(self, resultPtr):
    if resultPtr == IntPtr(0) and self._dispatcher.mapper.LastException == None:
        raise StopIteration()

_ironclad_class_attrs['__raise_stop'] = __raise_stop

def next(self):
    return self._dispatcher.method_selfarg('{0}tp_iternext', self, self.__raise_stop)
_ironclad_class_attrs['next'] = next
";

        public const string NOARGS_METHOD_CODE = @"
def {0}(self):
    '''{1}'''
    return self._dispatcher.method_noargs('{2}{0}', self)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string OBJARG_METHOD_CODE = @"
def {0}(self, arg):
    '''{1}'''
    return self._dispatcher.method_objarg('{2}{0}', self, arg)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string SWAPPEDOBJARG_METHOD_CODE = @"
def {0}(self, arg):
    '''{1}'''
    return self._dispatcher.method_objarg('{2}{0}', arg, self)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string VARARGS_METHOD_CODE = @"
def {0}(self, *args):
    '''{1}'''
    return self._dispatcher.method_varargs('{2}{0}', self, *args)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string VARARGS_KWARGS_METHOD_CODE = @"
def {0}(self, *args, **kwargs):
    '''{1}'''
    return self._dispatcher.method_kwargs('{2}{0}', self, *args, **kwargs)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string SSIZEARG_METHOD_CODE = @"
def {0}(self, ssize):
    '''{1}'''
    return self._dispatcher.method_ssizearg('{2}{0}', self, ssize)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string SSIZEOBJARG_METHOD_CODE = @"
def {0}(self, ssize, obj):
    '''{1}'''
    return self._dispatcher.method_ssizeobjarg('{2}{0}', self, ssize, obj)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string SSIZESSIZEARG_METHOD_CODE = @"
def {0}(self, ssize1, ssize2):
    '''{1}'''
    return self._dispatcher.method_ssizessizearg('{2}{0}', self, ssize1, ssize2)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string SSIZESSIZEOBJARG_METHOD_CODE = @"
def {0}(self, ssize1, ssize2, obj):
    '''{1}'''
    return self._dispatcher.method_ssizessizeobjarg('{2}{0}', self, ssize1, ssize2, obj)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string SELFARG_METHOD_CODE = @"
def {0}(self):
    '''{1}'''
    return self._dispatcher.method_selfarg('{2}{0}', self)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string LENFUNC_METHOD_CODE = @"
def {0}(self):
    '''{1}'''
    return self._dispatcher.method_lenfunc('{2}{0}', self)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string OBJOBJARG_METHOD_CODE = @"
def {0}(self, arg1, arg2):
    '''{1}'''
    return self._dispatcher.method_objobjarg('{2}{0}', self, arg1, arg2)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string TERNARY_METHOD_CODE = @"
def {0}(self, arg1, arg2=None):
    '''{1}'''
    return self._dispatcher.method_ternary('{2}{0}', self, arg1, arg2)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string SWAPPEDTERNARY_METHOD_CODE = @"
def {0}(self, arg):
    '''{1}'''
    return self._dispatcher.method_ternary_swapped('{2}{0}', self, arg)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string INQURY_METHOD_CODE = @"
def {0}(self):
    '''{1}'''
    return self._dispatcher.method_inquiry('{2}{0}', self)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string RICHCMP_METHOD_CODE = @"
def _ironclad_lt(self, other):
    return self._dispatcher.method_richcmp('{0}tp_richcompare', self, other, 0)
def _ironclad_le(self, other):
    return self._dispatcher.method_richcmp('{0}tp_richcompare', self, other, 1)
def _ironclad_eq(self, other):
    return self._dispatcher.method_richcmp('{0}tp_richcompare', self, other, 2)
def _ironclad_ne(self, other):
    return self._dispatcher.method_richcmp('{0}tp_richcompare', self, other, 3)
def _ironclad_gt(self, other):
    return self._dispatcher.method_richcmp('{0}tp_richcompare', self, other, 4)
def _ironclad_ge(self, other):
    return self._dispatcher.method_richcmp('{0}tp_richcompare', self, other, 5)

_ironclad_class_attrs['__lt__'] = _ironclad_lt
_ironclad_class_attrs['__le__'] = _ironclad_le
_ironclad_class_attrs['__eq__'] = _ironclad_eq
_ironclad_class_attrs['__ne__'] = _ironclad_ne
_ironclad_class_attrs['__gt__'] = _ironclad_gt
_ironclad_class_attrs['__ge__'] = _ironclad_ge
";

        public const string COMPARE_METHOD_CODE = @"
def {0}(self, other):
    '''{1}'''
    return self._dispatcher.method_cmpfunc('{2}{0}', self, other)

_ironclad_class_attrs['{0}'] = {0}
";

        public const string HASH_METHOD_CODE = @"
def {0}(self):
    '''{1}'''
    return self._dispatcher.method_hashfunc('{2}{0}', self)
_ironclad_class_attrs['{0}'] = {0}
";

        public const string NOARGS_FUNCTION_CODE = @"
def {0}():
    '''{1}'''
    return _dispatcher.function_noargs('{2}{0}')
";

        public const string OBJARG_FUNCTION_CODE = @"
def {0}(arg):
    '''{1}'''
    return _dispatcher.function_objarg('{2}{0}', arg)
";

        public const string VARARGS_FUNCTION_CODE = @"
def {0}(*args):
    '''{1}'''
    return _dispatcher.function_varargs('{2}{0}', *args)
";

        public const string VARARGS_KWARGS_FUNCTION_CODE = @"
def {0}(*args, **kwargs):
    '''{1}'''
    return _dispatcher.function_kwargs('{2}{0}', *args, **kwargs)
";
    }
}
