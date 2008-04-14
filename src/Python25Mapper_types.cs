
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Types;


namespace Ironclad
{

    public partial class Python25Mapper
    {


        public override void 
        Fill_PyFile_Type(IntPtr address)
        {
            this.StoreUnmanagedData(address, TypeCache.PythonFile);
        }
        
        public override int
        PyType_IsSubtype(IntPtr subtypePtr, IntPtr typePtr)
        {
            IPythonType subtype = (IPythonType)this.Retrieve(subtypePtr);
            bool result = subtype.IsSubclassOf(this.Retrieve(typePtr));
            if (result)
            {
                return 1;
            }
            return 0;
        }
    }
}
