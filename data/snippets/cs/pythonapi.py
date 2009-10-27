
from common import FILE_TEMPLATE

#================================================================================================

PYTHONAPI_TEMPLATE = """\
    public class PythonApi
    {
        protected Dictionary<string, Delegate> dgtMap = new Dictionary<string, Delegate>();
        private Dictionary<string, IntPtr> dataMap = new Dictionary<string, IntPtr>();

%s

        public virtual IntPtr GetAddress(string name)
        {
            if (this.dgtMap.ContainsKey(name))
            {
                return Marshal.GetFunctionPointerForDelegate(this.dgtMap[name]);
            }

            switch (name)
            {
%s

                default:
                    return IntPtr.Zero;
            }
            return Marshal.GetFunctionPointerForDelegate(this.dgtMap[name]);
        }


%s

        public void SetData(string name, IntPtr address)
        {
            switch (name)
            {
%s
            }
        }
    }"""

PYTHONAPI_FILE_TEMPLATE = FILE_TEMPLATE % PYTHONAPI_TEMPLATE

#================================================================================================

PYTHONAPI_METHOD_TEMPLATE = """\
        public virtual %(return_type)s %(symbol)s(%(arglist)s)
        {
            throw new NotImplementedException("called %(symbol)s");
        }"""
        
PYTHONAPI_METHOD_CASE = """\
                case "%(symbol)s":
                    this.dgtMap[name] = new dgt_%(dgt_type)s(this.%(symbol)s);
                    break;"""

#================================================================================================
        
PYTHONAPI_NOT_IMPLEMENTED_METHOD_TEMPLATE = """\
        public void %(symbol)s()
        {
            Console.WriteLine("Error: %(symbol)s is not yet implemented");
            throw new NotImplementedException("%(symbol)s");
        }"""
                    
PYTHONAPI_NOT_IMPLEMENTED_METHOD_CASE = """\
                case "%(symbol)s":
                    this.dgtMap[name] = new dgt_void_void(this.%(symbol)s);
                    break;"""

#================================================================================================

PYTHONAPI_DATA_ITEM_TEMPLATE = """\
        public virtual void Fill_%(symbol)s(IntPtr address) { ; }
        public IntPtr %(symbol)s
        {
            get
            {
                IntPtr address;
                if (this.dataMap.TryGetValue("%(symbol)s", out address))
                {
                    return address;
                }
                return IntPtr.Zero;
            }
        }"""

PYTHONAPI_DATA_ITEM_CASE = """\
                case "%(symbol)s":
                    this.Fill_%(symbol)s(address);
                    this.dataMap["%(symbol)s"] = address;
                    break;"""