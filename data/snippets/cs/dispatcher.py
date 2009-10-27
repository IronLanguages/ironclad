
from common import FILE_TEMPLATE

#================================================================================================

DISPATCHER_TEMPLATE = """\
    public partial class Dispatcher
    {
%s
    }"""

DISPATCHER_FILE_TEMPLATE = FILE_TEMPLATE % DISPATCHER_TEMPLATE

#================================================================================================

FIELD_TEMPLATE = """\
        public %(cstype)s get_%(name)s_field(object instance, int offset)
        {
            this.mapper.EnsureGIL();
            try
            {
                IntPtr instancePtr = this.mapper.Store(instance);
                IntPtr address = CPyMarshal.Offset(instancePtr, offset);
                %(cstype)s ret = %(gettweak)s(CPyMarshal.Read%(cpmtype)s(address));
                this.mapper.DecRef(instancePtr);
                return ret;
            }
            finally
            {
                this.mapper.ReleaseGIL();
            }
        }
        public void set_%(name)s_field(object instance, int offset, %(cstype)s value)
        {
            this.mapper.EnsureGIL();
            try
            {
                IntPtr instancePtr = this.mapper.Store(instance);
                IntPtr address = CPyMarshal.Offset(instancePtr, offset);
                CPyMarshal.Write%(cpmtype)s(address, %(settweak)s(value));
                this.mapper.DecRef(instancePtr);
            }
            finally
            {
                this.mapper.ReleaseGIL();
            }
        }"""

#================================================================================================

METHOD_TEMPLATE = """\
        %(signature)s
        {
            this.mapper.EnsureGIL();
            try
            {
%(translate_objs)s
                %(store_ret)s%(call)s
%(cleanup_objs)s
                %(handle_ret)s
                PythonExceptions.BaseException error = (PythonExceptions.BaseException)this.mapper.LastException;
                if (error != null)
                {
                    this.mapper.LastException = null;
                    throw error.clsException;
                }
                %(return_ret)s
            }
            finally
            {
                this.mapper.ReleaseGIL();
            }
        }"""

SIGNATURE_TEMPLATE = "public %(rettype)s %(name)s(%(arglist)s)"

CALL_TEMPLATE = "((dgt_%(dgttype)s)(this.table[key]))(%(arglist)s);"

TRANSLATE_OBJ_TEMPLATE = """\
                IntPtr ptr%(index)d = this.mapper.Store(arg%(index)d);"""

TRANSLATE_NULLABLEKWARGS_TEMPLATE = """\
                IntPtr ptr%(index)d = IntPtr.Zero;
                if (Builtin.len(arg%(index)d) > 0)
                {
                    ptr%(index)d = this.mapper.Store(arg%(index)d);
                }"""

CLEANUP_OBJ_TEMPLATE = """\
                if (ptr%(index)d != IntPtr.Zero)
                {
                    this.mapper.DecRef(ptr%(index)d);
                }"""

NULL_ARG = 'IntPtr.Zero'

MODULE_ARG = 'this.modulePtr'

ASSIGN_RETPTR = 'IntPtr retptr = '

ASSIGN_RET_TEMPLATE = '%s ret = '

HANDLE_RET_NULL = """object ret = null;
                if (retptr == IntPtr.Zero)
                {
                    if (this.mapper.LastException == null)
                    {
                        this.mapper.LastException = %s;
                    }
                }
                else
                {
                    ret = this.mapper.Retrieve(retptr);
                    this.mapper.DecRef(retptr);
                }"""

DEFAULT_HANDLE_RETPTR = HANDLE_RET_NULL % 'new NullReferenceException(key)'

ITERNEXT_HANDLE_RETPTR = HANDLE_RET_NULL % 'PythonOps.StopIteration()'
                
THROW_RET_NEGATIVE = """if (ret < 0)
                {
                    if (this.mapper.LastException == null)
                    {
                        this.mapper.LastException = new Exception(key);
                    }
                }"""

HANDLE_RET_DESTRUCTOR = """this.mapper.DecRef(ptr0);
                this.mapper.Unmap(ptr0);"""

SIMPLE_RETURN = 'return ret;'