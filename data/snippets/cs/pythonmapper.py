
from common import FILE_TEMPLATE


#================================================================================================

PYTHONMAPPER_TEMPLATE = """\
    public partial class PythonMapper : PythonApi
    {
%s
    }"""

PYTHONMAPPER_FILE_TEMPLATE = FILE_TEMPLATE % PYTHONMAPPER_TEMPLATE


#================================================================================================

EXCEPTION_TEMPLATE = """\
        public override void Fill_PyExc_%(name)s(IntPtr addr)
        {
            IntPtr value = this.Store(PythonExceptions.%(name)s);
            CPyMarshal.WritePtr(addr, value);
        }"""


#================================================================================================

STOREDISPATCH_TEMPLATE = """\
        private IntPtr StoreDispatch(object obj)
        {
%s
            return this.StoreObject(obj);
        }"""

STOREDISPATCH_TYPE_TEMPLATE = """\
            if (obj is %(type)s) { return this.StoreTyped((%(type)s)obj); }"""


#================================================================================================

OPERATOR_TEMPLATE = """\
        public override IntPtr
        %(name)s(IntPtr arg1ptr, IntPtr arg2ptr)
        {
            try
            {
                object result = PythonOperator.%(operator)s(this.scratchContext, this.Retrieve(arg1ptr), this.Retrieve(arg2ptr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }"""


#================================================================================================

C2PY_TEMPLATE = """\
        public override IntPtr
        %(name)s(%(type)s value)
        {
            return this.Store(%(cast)svalue);
        }"""


#================================================================================================

PY2C_TEMPLATE = """\
        public override %(type)s
        %(name)s(IntPtr valuePtr)
        {
            try
            {
                return this.%(converter)s(this.Retrieve(valuePtr))%(coerce)s;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return %(default)s;
            }
        }"""


#================================================================================================

FILL_TYPES_TEMPLATE = """\
        public override void
        Fill_%(name)s(IntPtr ptr)
        {
            CPyMarshal.Zero(ptr, Marshal.SizeOf(typeof(PyTypeObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyTypeObject), "ob_refcnt", 1);
%(extra)s
            this.map.Associate(ptr, %(type)s);
        }"""

FILL_TYPES_NUMBER_TEMPLATE = """\
            this.%(data)s(ptr);"""

FILL_TYPES_SIZE_TEMPLATE = """\
            CPyMarshal.WriteIntField(ptr, typeof(PyTypeObject), "%(slot)s", Marshal.SizeOf(typeof(%(data)s)));"""

FILL_TYPES_DEFAULT_TEMPLATE = """\
            CPyMarshal.WritePtrField(ptr, typeof(PyTypeObject), "%(slot)s", this.GetAddress("%(data)s"));"""

FILL_TYPES_SLOT_TEMPLATES = {
    "tp_as_number": FILL_TYPES_NUMBER_TEMPLATE,
    "tp_basicsize": FILL_TYPES_SIZE_TEMPLATE,
    "tp_itemsize": FILL_TYPES_SIZE_TEMPLATE,
}