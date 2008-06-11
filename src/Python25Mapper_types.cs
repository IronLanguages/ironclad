using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Ironclad.Structs;


namespace Ironclad
{

    public partial class Python25Mapper
    {
        public override void 
        Fill_PyFile_Type(IntPtr address)
        {
            this.map.Associate(address, TypeCache.PythonFile);
        }

        public override void
        Fill_PyInt_Type(IntPtr address)
        {
            this.map.Associate(address, TypeCache.Int32);
        }

        public override void
        Fill_PyLong_Type(IntPtr address)
        {
            this.map.Associate(address, TypeCache.BigInteger);
        }

        public override void
        Fill_PyFloat_Type(IntPtr address)
        {
            this.map.Associate(address, TypeCache.Double);
        }
        
        public override int
        PyType_IsSubtype(IntPtr subtypePtr, IntPtr typePtr)
        {
            PythonType subtype = (PythonType)this.Retrieve(subtypePtr);
            bool result = Builtin.issubclass(subtype, this.Retrieve(typePtr));
            if (result)
            {
                return 1;
            }
            return 0;
        }
        
        public override int
        PyType_Ready(IntPtr typePtr)
        {
            // optimism :)
            return 0;
        }
        
        public override IntPtr 
        PyType_GenericNew(IntPtr typePtr, IntPtr args, IntPtr kwargs)
        {
            PyType_GenericAlloc_Delegate dgt = (PyType_GenericAlloc_Delegate)CPyMarshal.ReadFunctionPtrField(
                typePtr, typeof(PyTypeObject), "tp_alloc", typeof(PyType_GenericAlloc_Delegate));
            return dgt(typePtr, 0);
        }
        
        public override IntPtr 
        PyType_GenericAlloc(IntPtr typePtr, int nItems)
        {
            int size = CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), "tp_basicsize");
            
            if (nItems > 0)
            {
                int itemsize = CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), "tp_itemsize");
                size += (nItems * itemsize);
            }
            
            IntPtr newInstance = this.allocator.Alloc(size);
            CPyMarshal.Zero(newInstance, size);
            CPyMarshal.WriteIntField(newInstance, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(newInstance, typeof(PyObject), "ob_type", typePtr);
            
            return newInstance;
        }
    }
}
