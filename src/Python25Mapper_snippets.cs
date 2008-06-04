namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        private const string FIX_RuntimeType_CODE = @"
CPyMarshal = CPyMarshal() # eww
";

        private const string NOARGS_FUNCTION_CODE = @"
def {0}():
    '''{1}'''
    return _dispatcher.function_noargs('{2}{0}')
";

        private const string OBJARG_FUNCTION_CODE = @"
def {0}(arg):
    '''{1}'''
    return _dispatcher.function_objarg('{2}{0}', arg)
";

        private const string VARARGS_FUNCTION_CODE = @"
def {0}(*args):
    '''{1}'''
    return _dispatcher.function_varargs('{2}{0}', *args)
";

        private const string VARARGS_KWARGS_FUNCTION_CODE = @"
def {0}(*args, **kwargs):
    '''{1}'''
    return _dispatcher.function_kwargs('{2}{0}', *args, **kwargs)
";

        private const string CLASS_CODE = @"
class {0}(object):
    '''{2}'''
    __module__ = '{1}'
    def __new__(cls, *args, **kwargs):
        return cls._dispatcher.construct('{0}.tp_new', cls, *args, **kwargs)
    
    def __init__(self, *args, **kwargs):
        self._dispatcher.init('{0}.tp_init', self, *args, **kwargs)
    
    def __del__(self):
        self._dispatcher.delete('{0}.tp_dealloc', self)
";

        private const string INT_MEMBER_GETTER_CODE = @"
    def {0}(self):
        fieldPtr = CPyMarshal.Offset(self._instancePtr, {1})
        return self._dispatcher.get_member_int(fieldPtr)
";

        private const string INT_MEMBER_SETTER_CODE = @"
    def {0}(self, value):
        fieldPtr = CPyMarshal.Offset(self._instancePtr, {1})
        self._dispatcher.set_member_int(fieldPtr, value)
";

        private const string OBJECT_MEMBER_GETTER_CODE = @"
    def {0}(self):
        fieldPtr = CPyMarshal.Offset(self._instancePtr, {1})
        return self._dispatcher.get_member_object(fieldPtr)
";

        private const string OBJECT_MEMBER_SETTER_CODE = @"
    def {0}(self, value):
        fieldPtr = CPyMarshal.Offset(self._instancePtr, {1})
        self._dispatcher.set_member_object(fieldPtr, value)
";

        private const string GETTER_METHOD_CODE = @"
    def {0}(self):
        return self._dispatcher.method_getter('{1}{0}', self._instancePtr, IntPtr({2}))
";

        private const string SETTER_METHOD_CODE = @"
    def {0}(self, value):
        return self._dispatcher.method_setter('{1}{0}', self._instancePtr, value, IntPtr({2}))
";

        private const string PROPERTY_CODE = @"
    {0} = property({1}, {2}, None, '''{3}''')
";

        private const string ITER_METHOD_CODE = @"
    def __iter__(self):
        return self._dispatcher.method_selfarg('{0}tp_iter', self._instancePtr)
";

        private const string ITERNEXT_METHOD_CODE = @"
    def __raise_stop(self, resultPtr):
        if resultPtr == IntPtr(0) and self._dispatcher.mapper.LastException == None:
                raise StopIteration()

    def next(self):
        return self._dispatcher.method_selfarg('{0}tp_iternext', self._instancePtr, self.__raise_stop)
";

        private const string NOARGS_METHOD_CODE = @"
    def {0}(self):
        '''{1}'''
        return self._dispatcher.method_noargs('{2}{0}', self._instancePtr)
";

        private const string OBJARG_METHOD_CODE = @"
    def {0}(self, arg):
        '''{1}'''
        return self._dispatcher.method_objarg('{2}{0}', self._instancePtr, arg)
";

        private const string VARARGS_METHOD_CODE = @"
    def {0}(self, *args):
        '''{1}'''
        return self._dispatcher.method_varargs('{2}{0}', self._instancePtr, *args)
";

        private const string VARARGS_KWARGS_METHOD_CODE = @"
    def {0}(self, *args, **kwargs):
        '''{1}'''
        return self._dispatcher.method_kwargs('{2}{0}', self._instancePtr, *args, **kwargs)
";
        private const string INSTALL_IMPORT_HOOK_CODE = @"
import ihooks
import imp

class _IroncladHooks(ihooks.Hooks):

    def get_suffixes(self):
        suffixes = [('.pyd', 'rb', imp.C_EXTENSION)]
        suffixes.extend(imp.get_suffixes())
        return suffixes

    def load_dynamic(self, name, filename, file):
        _mapper.LoadModule(filename, name)
        module = _mapper.GetModule(name)
        self.modules_dict()[name] = module
        return module


class _IroncladModuleImporter(ihooks.ModuleImporter):

    # copied from ihooks.py
    def determine_parent(self, globals):
        if not globals or not '__name__' in globals:
            return None
        pname = globals['__name__']
        if '__path__' in globals:
            parent = self.modules[pname]
            # 'assert globals is parent.__dict__' always fails --
            # I think an ipy module dict is some sort of funky 
            # wrapper around a Scope, so the underlying data store
            # actually is the same.
            assert globals == parent.__dict__
            return parent
        if '.' in pname:
            i = pname.rfind('.')
            pname = pname[:i]
            parent = self.modules[pname]
            assert parent.__name__ == pname
            return parent
        return None

_importer = _IroncladModuleImporter()
_importer.set_hooks(_IroncladHooks())
_importer.install()
";
    }
}