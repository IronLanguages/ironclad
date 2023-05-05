using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Microsoft.Scripting;

using Ironclad.Structs;


namespace Ironclad
{

    public partial class PythonMapper
    {
        public override IntPtr 
        PyType_GenericNew(IntPtr typePtr, IntPtr args, IntPtr kwargs)
        {
            dgt_ptr_ptrssize dgt = CPyMarshal.ReadFunctionPtrField<dgt_ptr_ptrssize>(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_alloc));
            return dgt(typePtr, 0);
        }
        
        public override IntPtr 
        PyType_GenericAlloc(IntPtr typePtr, nint nItems)
        {
            nint size = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_basicsize));
            if (nItems > 0)
            {
                nint itemsize = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_itemsize));
                size += (nItems * itemsize);
            }
            
            IntPtr newInstance = this.allocator.Alloc(size);
            CPyMarshal.Zero(newInstance, size);
            CPyMarshal.WritePtrField(newInstance, typeof(PyObject), nameof(PyObject.ob_refcnt), 1);
            CPyMarshal.WritePtrField(newInstance, typeof(PyObject), nameof(PyObject.ob_type), typePtr);

            if (nItems > 0)
            {
                CPyMarshal.WritePtrField(newInstance, typeof(PyVarObject), nameof(PyVarObject.ob_size), nItems);
            }

            return newInstance;
        }
        
        public override int
        PyType_IsSubtype(IntPtr subtypePtr, IntPtr typePtr)
        {
            if (subtypePtr == IntPtr.Zero || typePtr == IntPtr.Zero)
            {
                return 0;
            }
            if (subtypePtr == typePtr || typePtr == PyBaseObject_Type)
            {
                return 1;
            }
            PythonType subtype = this.Retrieve(subtypePtr) as PythonType;
            if (!this.HasPtr(typePtr))
            {
                return 0;
            }
            PythonType _type = this.Retrieve(typePtr) as PythonType;
            if (subtype == null || _type == null)
            {
                return 0;
            }
            if (Builtin.issubclass(this.scratchContext, subtype, _type))
            {
                return 1;
            }
            return 0;
        }
        
        public override int
        PyType_Ready(IntPtr typePtr)
        {
            if (typePtr == IntPtr.Zero)
            {
                return -1;
            }
            Py_TPFLAGS flags = (Py_TPFLAGS)CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_flags));
            if ((Int32)(flags & (Py_TPFLAGS.READY | Py_TPFLAGS.READYING)) != 0)
            {
                return 0;
            }
            flags |= Py_TPFLAGS.READYING;
            CPyMarshal.WriteIntField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_flags), (Int32)flags);
            
            IntPtr typeTypePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.ob_type));
            if ((typeTypePtr == IntPtr.Zero) && (typePtr != this.PyType_Type))
            {
                CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.ob_type), this.PyType_Type);
            }

            IntPtr typeBasePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_base));
            if ((typeBasePtr == IntPtr.Zero) && (typePtr != this.PyBaseObject_Type))
            {
                typeBasePtr = this.PyBaseObject_Type;
                CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_base), typeBasePtr);
            }

            PyType_Ready(typeBasePtr);
            this.InheritSubclassFlags(typePtr);
            this.InheritPtrField(typePtr, nameof(PyTypeObject.tp_alloc));
            this.InheritPtrField(typePtr, nameof(PyTypeObject.tp_new));
            this.InheritPtrField(typePtr, nameof(PyTypeObject.tp_dealloc));
            this.InheritPtrField(typePtr, nameof(PyTypeObject.tp_free));
            this.InheritPtrField(typePtr, nameof(PyTypeObject.tp_doc));
            this.InheritPtrField(typePtr, nameof(PyTypeObject.tp_call));
            this.InheritPtrField(typePtr, nameof(PyTypeObject.tp_as_number));
            this.InheritPtrField(typePtr, nameof(PyTypeObject.tp_as_sequence));
            this.InheritPtrField(typePtr, nameof(PyTypeObject.tp_as_mapping));
            this.InheritPtrField(typePtr, nameof(PyTypeObject.tp_as_buffer));
            this.InheritPtrField(typePtr, nameof(PyTypeObject.tp_basicsize));
            this.InheritPtrField(typePtr, nameof(PyTypeObject.tp_itemsize));

            if (!this.HasPtr(typePtr))
            {
                this.Retrieve(typePtr);
            }
            else
            {
                object klass = this.Retrieve(typePtr);
                if (Builtin.hasattr(this.scratchContext, klass, "__dict__"))
                {
                    object typeDict = Builtin.getattr(this.scratchContext, klass, "__dict__");
                    CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_dict), this.Store(typeDict));
                }
            }

            flags = (Py_TPFLAGS)CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_flags));
            flags |= Py_TPFLAGS.READY;
            flags &= ~Py_TPFLAGS.READYING;
            CPyMarshal.WriteIntField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_flags), (Int32)flags);
            return 0;
        }

        public override IntPtr
        IC_PyType_New(IntPtr typePtr, IntPtr argsPtr, IntPtr kwargsPtr)
        {
            try
            {
                // we ignore typePtr; see IC_PyType_New_Test
                PythonTuple args = (PythonTuple)this.Retrieve(argsPtr);
                if (kwargsPtr != IntPtr.Zero)
                {
                    throw new NotImplementedException("IC_PyType_New; non-null kwargs; please submit a bug (with repro)");
                }
                return this.Store(new PythonType(
                    this.scratchContext, (string)args[0], (PythonTuple)args[1], (PythonDictionary)args[2]));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        public void
        ReadyBuiltinTypes()
        {
            this.PyType_Ready(this.PyType_Type);
            this.PyType_Ready(this.PyBaseObject_Type);
            this.PyType_Ready(this.PyLong_Type);
            this.PyType_Ready(this.PyBool_Type); // note: bool should come after int, because bools are ints
            this.PyType_Ready(this.PyFloat_Type);
            this.PyType_Ready(this.PyComplex_Type);
            this.PyType_Ready(this.PyBytes_Type);
            this.PyType_Ready(this.PyTuple_Type);
            this.PyType_Ready(this.PyList_Type);
            this.PyType_Ready(this.PyDict_Type);
            this.PyType_Ready(this._PyNone_Type);
            this.PyType_Ready(this.PySlice_Type);
            this.PyType_Ready(this.PyEllipsis_Type);
            this.PyType_Ready(this._PyNotImplemented_Type);
            this.PyType_Ready(this.PyMethod_Type);
            this.PyType_Ready(this.PyFunction_Type);

            this.actualisableTypes[this.PyType_Type] = new ActualiseDelegate(this.ActualiseType);
            this.actualisableTypes[this.PyFloat_Type] = new ActualiseDelegate(this.ActualiseFloat);
        }
                
        private void
        InheritPtrField(IntPtr typePtr, string name)
        {
            IntPtr fieldPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), name);
            if (fieldPtr == IntPtr.Zero)
            {
                IntPtr basePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_base));
                if (basePtr != IntPtr.Zero)
                {
                    CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), name, 
                        CPyMarshal.ReadPtrField(basePtr, typeof(PyTypeObject), name));
                }
            }
        }
                
        private void
        InheritIntField(IntPtr typePtr, string name)
        {
            int fieldVal = CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), name);
            if (fieldVal == 0)
            {
                IntPtr basePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_base));
                if (basePtr != IntPtr.Zero)
                {
                    CPyMarshal.WriteIntField(typePtr, typeof(PyTypeObject), name,
                        CPyMarshal.ReadIntField(basePtr, typeof(PyTypeObject), name));
                }
            }
        }
        
        private void
        InheritSubclassFlags(IntPtr typePtr)
        {
            Py_TPFLAGS flags = (Py_TPFLAGS)CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_flags));
            
            if (this.PyType_IsSubtype(typePtr, this.PyLong_Type) != 0) { flags |= Py_TPFLAGS.LONG_SUBCLASS; }
            if (this.PyType_IsSubtype(typePtr, this.PyList_Type) != 0) { flags |= Py_TPFLAGS.LIST_SUBCLASS; }
            if (this.PyType_IsSubtype(typePtr, this.PyTuple_Type) != 0) { flags |= Py_TPFLAGS.TUPLE_SUBCLASS; }
            if (this.PyType_IsSubtype(typePtr, this.PyBytes_Type) != 0) { flags |= Py_TPFLAGS.BYTES_SUBCLASS; }
            if (this.PyType_IsSubtype(typePtr, this.PyUnicode_Type) != 0) { flags |= Py_TPFLAGS.UNICODE_SUBCLASS; }
            if (this.PyType_IsSubtype(typePtr, this.PyDict_Type) != 0) { flags |= Py_TPFLAGS.DICT_SUBCLASS; }
            if (this.PyType_IsSubtype(typePtr, this.PyType_Type) != 0) { flags |= Py_TPFLAGS.TYPE_SUBCLASS; }
            // TODO: PyExc_BaseException is tedious
            
            CPyMarshal.WriteIntField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_flags), (Int32)flags);
        }

        private IntPtr
        StoreTyped(PythonType _type)
        {
            int typeSize = Marshal.SizeOf<PyTypeObject>();
            IntPtr typePtr = this.allocator.Alloc(typeSize);
            CPyMarshal.Zero(typePtr, typeSize);
            
            CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.ob_refcnt), 2);

            object ob_type = PythonCalls.Call(this.scratchContext, Builtin.type, new object[] { _type });
            CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.ob_type), this.Store(ob_type));
            
            string tp_name = (string)_type.__getattribute__(this.scratchContext, "__name__");
            CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_name), this.Store(tp_name));
            
            PythonTuple tp_bases = (PythonTuple)_type.__getattribute__(this.scratchContext, "__bases__");
            object tp_base = tp_bases[0];
            CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_base), this.Store(tp_base));
            if (tp_bases.__len__() > 1)
            {
                CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_bases), this.Store(tp_bases));
            }

            this.scratchModule.Get__dict__()["_ironclad_bases"] = tp_bases;
            this.scratchModule.Get__dict__()["_ironclad_metaclass"] = ob_type;
            this.ExecInModule(CodeSnippets.CLASS_STUB_CODE, this.scratchModule);
            this.classStubs[typePtr] = this.scratchModule.Get__dict__()["_ironclad_class_stub"];

            this.actualisableTypes[typePtr] = new ActualiseDelegate(this.ActualiseArbitraryObject);
            this.map.Associate(typePtr, _type);
            this.PyType_Ready(typePtr);
            return typePtr;
        }

        private void
        ActualiseFloat(IntPtr fptr)
        {
            double value = CPyMarshal.ReadDoubleField(fptr, typeof(PyFloatObject), nameof(PyFloatObject.ob_fval));
            this.map.Associate(fptr, value);
        }
        
        private void 
        ActualiseType(IntPtr typePtr)
        {
            this.PyType_Ready(typePtr);
            object klass = this.GenerateClass(typePtr);
            this.actualisableTypes[typePtr] = new ActualiseDelegate(this.ActualiseArbitraryObject);
            
            this.map.Associate(typePtr, klass);
            this.IncRef(typePtr);
        }
        
        private void
        ActualiseArbitraryObject(IntPtr ptr)
        {
            IntPtr typePtr = CPyMarshal.ReadPtrField(ptr, typeof(PyObject), nameof(PyObject.ob_type));
            PythonType type_ = (PythonType)this.Retrieve(typePtr);
            
            object[] args = new object[]{};
            if (Builtin.issubclass(this.scratchContext, type_, TypeCache.Int32))
            {
                throw new InvalidOperationException(); // TODO: get rid of TypeCache.Int32? https://github.com/IronLanguages/ironclad/issues/14
            }
            if (Builtin.issubclass(this.scratchContext, type_, TypeCache.Double))
            {
                args = new object[] { CPyMarshal.ReadDoubleField(ptr, typeof(PyFloatObject), nameof(PyFloatObject.ob_fval)) };
            }
            if (Builtin.issubclass(this.scratchContext, type_, TypeCache.Bytes))
            {
                args = new object[] { this.ReadPyBytes(ptr) };
            }
            if (Builtin.issubclass(this.scratchContext, type_, TypeCache.PythonType))
            {
                string name = CPyMarshal.ReadCStringField(ptr, typeof(PyTypeObject), nameof(PyTypeObject.tp_name));
                PythonTuple tp_bases = this.ExtractBases(typePtr);
                args = new object[] { name, tp_bases, new PythonDictionary() };
            }
            
            object obj = PythonCalls.Call(this.classStubs[typePtr], args);
            Builtin.setattr(this.scratchContext, obj, "__class__", type_);
            this.StoreBridge(ptr, obj);
            this.IncRef(ptr);
            GC.KeepAlive(obj); // TODO: please test me, if you can work out how to
        }
    }
}
