using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Calls;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Ironclad.Structs;


namespace Ironclad
{

    public partial class Python25Mapper
    {
        public override void
        Fill_PyEllipsis_Type(IntPtr address)
        {
            // not quite trivial to autogenerate
            // (surely there's a better way to get the Ellipsis object...)
            CPyMarshal.WriteIntField(address, typeof(PyTypeObject), "ob_refcnt", 1);
            object ellipsisType = PythonCalls.Call(Builtin.type, new object[] { PythonOps.Ellipsis });
            this.map.Associate(address, ellipsisType);
        }

        public override void
        Fill_PyBool_Type(IntPtr address)
        {
            // not quite trivial to autogenerate
            CPyMarshal.WriteIntField(address, typeof(PyTypeObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_base", this.PyInt_Type);
            this.map.Associate(address, TypeCache.Boolean);
        }

        private void
        AddDefaultNumberMethods(IntPtr typePtr)
        {
            int nmSize = Marshal.SizeOf(typeof(PyNumberMethods));
            IntPtr nmPtr = this.allocator.Alloc(nmSize);
            CPyMarshal.Zero(nmPtr, nmSize);

            CPyMarshal.WritePtrField(nmPtr, typeof(PyNumberMethods), "nb_float", this.GetAddress("PyNumber_Float"));
            CPyMarshal.WritePtrField(nmPtr, typeof(PyNumberMethods), "nb_int", this.GetAddress("PyNumber_Int"));

            CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), "tp_as_number", nmPtr);
        }
        
        public void
        ReadyBuiltinTypes()
        {
            this.PyType_Ready(this.PyType_Type);
            this.PyType_Ready(this.PyBaseObject_Type);
            this.PyType_Ready(this.PyInt_Type);
            this.PyType_Ready(this.PyBool_Type); // note: bool should come after int, because bools are ints
            this.PyType_Ready(this.PyLong_Type);
            this.PyType_Ready(this.PyFloat_Type);
            this.PyType_Ready(this.PyComplex_Type);
            this.PyType_Ready(this.PyString_Type);
            this.PyType_Ready(this.PyTuple_Type);
            this.PyType_Ready(this.PyList_Type);
            this.PyType_Ready(this.PyDict_Type);
            this.PyType_Ready(this.PyFile_Type);
            this.PyType_Ready(this.PyCObject_Type);
            this.PyType_Ready(this.PyNone_Type);
            this.PyType_Ready(this.PySlice_Type);
            this.PyType_Ready(this.PyEllipsis_Type);
            this.PyType_Ready(this.PySeqIter_Type);

            this.actualisableTypes[this.PyType_Type] = new ActualiseDelegate(this.ActualiseType);
        }
        
        public override int
        PyType_IsSubtype(IntPtr subtypePtr, IntPtr typePtr)
        {
            if (subtypePtr == IntPtr.Zero || typePtr == IntPtr.Zero)
            {
                return 0;
            }
            PythonType _type = this.Retrieve(typePtr) as PythonType;
            PythonType subtype = this.Retrieve(subtypePtr) as PythonType;
            if (subtype == null || _type == null)
            {
                return 0;
            }
            if (Builtin.issubclass(subtype, _type))
            {
                return 1;
            }
            return 0;
        }
        
                
        private void
        InheritPtrField(IntPtr typePtr, string name)
        {
            IntPtr fieldPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), name);
            if (fieldPtr == IntPtr.Zero)
            {
                IntPtr basePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_base");
                if (basePtr != IntPtr.Zero)
                {
                    CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), name,
                        CPyMarshal.ReadPtrField(basePtr, typeof(PyTypeObject), name));
                }
            }
        }
        
        public override int
        PyType_Ready(IntPtr typePtr)
        {
            if (typePtr == IntPtr.Zero)
            {
                return -1;
            }
            
            Py_TPFLAGS flags = (Py_TPFLAGS)CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), "tp_flags");
            if ((Int32)(flags & Py_TPFLAGS.READY) != 0)
            {
                return 0;
            }
            
            IntPtr typeTypePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "ob_type");
            if ((typeTypePtr == IntPtr.Zero) && (typePtr != this.PyType_Type))
            {
                CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), "ob_type", this.PyType_Type);
            }
            IntPtr typeBasePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_base");
            if ((typeBasePtr == IntPtr.Zero) && (typePtr != this.PyBaseObject_Type))
            {
                typeBasePtr = this.PyBaseObject_Type;
                CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), "tp_base", typeBasePtr);
            }
            PyType_Ready(typeBasePtr);
            
            this.InheritPtrField(typePtr, "tp_alloc");
            this.InheritPtrField(typePtr, "tp_init");
            this.InheritPtrField(typePtr, "tp_new");
            this.InheritPtrField(typePtr, "tp_dealloc");
            this.InheritPtrField(typePtr, "tp_free");
            this.InheritPtrField(typePtr, "tp_print");
            this.InheritPtrField(typePtr, "tp_repr");
            this.InheritPtrField(typePtr, "tp_str");
            this.InheritPtrField(typePtr, "tp_doc");
            this.InheritPtrField(typePtr, "tp_call");
            this.InheritPtrField(typePtr, "tp_as_number");
            this.InheritPtrField(typePtr, "tp_as_sequence");
            
            flags |= Py_TPFLAGS.READY;
            CPyMarshal.WriteIntField(typePtr, typeof(PyTypeObject), "tp_flags", (Int32)flags);
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


        private void
        ActualiseCPyObject(IntPtr ptr)
        {
            IntPtr typePtr = CPyMarshal.ReadPtrField(ptr, typeof(PyObject), "ob_type");
            object obj = PythonCalls.Call(this.trivialObjectSubclass);
            Builtin.setattr(DefaultContext.Default, obj, "_instancePtr", ptr);
            Builtin.setattr(DefaultContext.Default, obj, "__class__", this.Retrieve(typePtr));
            this.StoreBridge(ptr, obj);
            this.IncRef(ptr);
            GC.KeepAlive(obj); // please test me, if you can work out how to
        }

        
        private void 
        ActualiseType(IntPtr typePtr)
        {
            this.PyType_Ready(typePtr);
            this.GenerateClass(typePtr);
            this.actualisableTypes[typePtr] = new ActualiseDelegate(this.ActualiseCPyObject);
        }
    }
}
