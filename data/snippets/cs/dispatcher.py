
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
        public %(mgd_type)s get_%(name)s_field(object instance, int offset)
        {
            this.mapper.EnsureGIL();
            try
            {
                IntPtr instancePtr = this.mapper.Store(instance);
                IntPtr address = CPyMarshal.Offset(instancePtr, offset);
                %(mgd_type)s ret = %(get_tweak)s(CPyMarshal.Read%(cpm_suffix)s(address));
                this.mapper.DecRef(instancePtr);
                return ret;
            }
            finally
            {
                this.mapper.ReleaseGIL();
            }
        }
        public void set_%(name)s_field(object instance, int offset, %(mgd_type)s value)
        {
            this.mapper.EnsureGIL();
            try
            {
                IntPtr instancePtr = this.mapper.Store(instance);
                IntPtr address = CPyMarshal.Offset(instancePtr, offset);
                CPyMarshal.Write%(cpm_suffix)s(address, %(set_tweak)s(value));
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
%(store_ret)s
%(call_dgt)s
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


#================================================================================================

SIGNATURE_TEMPLATE = """\
        public %(rettype)s %(name)s(%(arglist)s)"""


#================================================================================================

CALL_DGT_TEMPLATE = """\
                    ((dgt_%(spec)s)(this.table[key]))(%(arglist)s);"""


#================================================================================================

TRANSLATE_OBJ_TEMPLATE = """\
                IntPtr ptr%(index)d = this.mapper.Store(arg%(index)d);"""

CLEANUP_OBJ_TEMPLATE = """\
                if (ptr%(index)d != IntPtr.Zero)
                {
                    this.mapper.DecRef(ptr%(index)d);
                }"""

TRANSLATE_NULLABLE_KWARGS_TEMPLATE = """\
                IntPtr ptr%(index)d = IntPtr.Zero;
                if (Builtin.len(arg%(index)d) > 0)
                {
                    ptr%(index)d = this.mapper.Store(arg%(index)d);
                }"""


#================================================================================================

NULL_ARG = 'IntPtr.Zero'

MODULE_ARG = 'this.modulePtr'


#================================================================================================

ASSIGN_RETPTR = """\
                IntPtr retptr = """

ASSIGN_RET_TEMPLATE = """\
                %s ret = """


#================================================================================================

SIMPLE_RETURN = """\
                return ret;"""


#================================================================================================

HANDLE_RET_NULL = """\
                object ret = null;
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
                

#================================================================================================

THROW_RET_NEGATIVE = """\
                if (ret < 0)
                {
                    if (this.mapper.LastException == null)
                    {
                        this.mapper.LastException = new Exception(key);
                    }
                }"""


#================================================================================================

HANDLE_RET_DESTRUCTOR = """\
                this.mapper.DecRef(ptr0);
                this.mapper.Unmap(ptr0);"""


