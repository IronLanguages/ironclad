namespace Ironclad
{
    internal partial class CodeSnippets
    {
        public const string USEFUL_IMPORTS = @"
from System import IntPtr, NullReferenceException
from Ironclad import CPyMarshal
";

        public const string NEW_EXCEPTION = @"
class {0}(Exception):
    __module__ = '{1}'
";

        public const string ACTUALISER_CODE = @"
class _ironclad_actualiser(_ironclad_class):
    def __new__(cls, *args, **kwargs):
        if issubclass(cls, int):
            return int.__new__(cls, args[0])
        if issubclass(cls, str):
            return str.__new__(cls, args[0])
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
    return cls._dispatcher.newfunc('{0}.tp_new', cls, args, kwargs)

def __del__(self):
    self._dispatcher.ic_destroy(self)

_ironclad_class_attrs['__new__'] = __new__
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
    return self._dispatcher.get_{2}_field(self, {1})
_ironclad_class_attrs['{0}'] = _ironclad_getter
";

        public const string MEMBER_SETTER_CODE = @"
def _ironclad_setter(self, value):
    self._dispatcher.set_{2}_field(self, {1}, value)
_ironclad_class_attrs['{0}'] = _ironclad_setter
";

        public const string GETTER_METHOD_CODE = @"
def _ironclad_getter(self):
    return self._dispatcher.ic_method_getter('{1}{0}', self, IntPtr({2}))
_ironclad_class_attrs['{0}'] = _ironclad_getter
";

        public const string SETTER_METHOD_CODE = @"
def _ironclad_setter(self, value):
    return self._dispatcher.ic_method_setter('{1}{0}', self, value, IntPtr({2}))
_ironclad_class_attrs['{0}'] = _ironclad_setter
";

        public const string PROPERTY_CODE = @"
_ironclad_class_attrs['{0}'] = property(_ironclad_getter, _ironclad_setter, None, '''{1}''')
";

        public const string COMPLEX_HACK_CODE = @"
def __complex__(self):
    return complex(float(self.real), float(self.imag))
_ironclad_class_attrs['__complex__'] = __complex__
";

        public const string NOARGS_FUNCTION_CODE = @"
def {0}():
    '''{1}'''
    return _dispatcher.ic_function_noargs('{2}{0}')
";

        public const string OBJARG_FUNCTION_CODE = @"
def {0}(arg):
    '''{1}'''
    return _dispatcher.ic_function_objarg('{2}{0}', arg)
";

        public const string VARARGS_FUNCTION_CODE = @"
def {0}(*args):
    '''{1}'''
    return _dispatcher.ic_function_varargs('{2}{0}', args)
";

        public const string VARARGS_KWARGS_FUNCTION_CODE = @"
def {0}(*args, **kwargs):
    '''{1}'''
    return _dispatcher.ic_function_kwargs('{2}{0}', args, kwargs)
";

        public const string NOARGS_METHOD_CODE = @"
def {0}(self):
    '''{1}'''
    return self._dispatcher.ic_method_noargs('{2}{0}', self)
_ironclad_class_attrs['{0}'] = {0}
";

        public const string OBJARG_METHOD_CODE = @"
def {0}(self, arg):
    '''{1}'''
    return self._dispatcher.ic_method_objarg('{2}{0}', self, arg)
_ironclad_class_attrs['{0}'] = {0}
";

        public const string VARARGS_METHOD_CODE = @"
def {0}(self, *args):
    '''{1}'''
    return self._dispatcher.ic_method_varargs('{2}{0}', self, args)
_ironclad_class_attrs['{0}'] = {0}
";

        public const string VARARGS_KWARGS_METHOD_CODE = @"
def {0}(self, *args, **kwargs):
    '''{1}'''
    return self._dispatcher.ic_method_kwargs('{2}{0}', self, args, kwargs)
_ironclad_class_attrs['{0}'] = {0}
";

        public const string RICHCMP_METHOD_CODE = @"
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
";
    }
}
