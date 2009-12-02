
from common import FILE_TEMPLATE


#================================================================================================

PYTHONAPI_TEMPLATE = """\
    public class PythonApi
    {
        private Dictionary<string, Delegate> dgts = new Dictionary<string, Delegate>();
        private Dictionary<string, IntPtr> data = new Dictionary<string, IntPtr>();

%(api_methods)s

        public IntPtr GetFuncPtr(string name)
        {
            if (this.dgts.ContainsKey(name))
            {
                return Marshal.GetFunctionPointerForDelegate(this.dgts[name]);
            }

            switch (name)
            {
%(getaddress_cases)s

                default:
                    return IntPtr.Zero;
            }
            return Marshal.GetFunctionPointerForDelegate(this.dgts[name]);
        }

%(data_properties)s

        public void RegisterData(string name, IntPtr address)
        {
            switch (name)
            {
%(setdata_cases)s
            }
        }
    }"""

PYTHONAPI_FILE_TEMPLATE = FILE_TEMPLATE % PYTHONAPI_TEMPLATE


#================================================================================================

METHOD_TEMPLATE = """\
        public virtual %(return_type)s %(symbol)s(%(arglist)s)
        {
            Console.WriteLine("Error: %(symbol)s is not yet implemented");
            throw new NotImplementedException("%(symbol)s");
        }"""
        
METHOD_NOT_IMPL_TEMPLATE = """\
        public void %(symbol)s()
        {
            Console.WriteLine("Error: %(symbol)s is not yet implemented");
            throw new NotImplementedException("%(symbol)s");
        }"""


#================================================================================================
        
GETADDRESS_CASE_TEMPLATE = """\
                case "%(symbol)s":
                    this.dgts[name] = new dgt_%(dgt_type)s(this.%(symbol)s);
                    break;"""
                    
GETADDRESS_CASE_NOT_IMPL_TEMPLATE = """\
                case "%(symbol)s":
                    this.dgts[name] = new dgt_void_void(this.%(symbol)s);
                    break;"""


#================================================================================================

DATA_PROPERTY_TEMPLATE = """\
        public virtual void Register_%(symbol)s(IntPtr address) { ; }
        public IntPtr %(symbol)s
        {
            get
            {
                IntPtr address;
                if (this.data.TryGetValue("%(symbol)s", out address))
                {
                    return address;
                }
                return IntPtr.Zero;
            }
        }"""


#================================================================================================

SETDATA_CASE_TEMPLATE = """\
                case "%(symbol)s":
                    this.Register_%(symbol)s(address);
                    this.data["%(symbol)s"] = address;
                    break;"""


#================================================================================================
