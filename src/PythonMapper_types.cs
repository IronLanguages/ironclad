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
            dgt_ptr_ptrsize dgt = (dgt_ptr_ptrsize)CPyMarshal.ReadFunctionPtrField(
                typePtr, typeof(PyTypeObject), "tp_alloc", typeof(dgt_ptr_ptrsize));
            return dgt(typePtr, 0);
        }
        
        public override IntPtr 
        PyType_GenericAlloc(IntPtr typePtr, uint nItems)
        {
            uint size = CPyMarshal.ReadUIntField(typePtr, typeof(PyTypeObject), "tp_basicsize");
            if (nItems > 0)
            {
                uint itemsize = CPyMarshal.ReadUIntField(typePtr, typeof(PyTypeObject), "tp_itemsize");
                size += (nItems * itemsize);
            }
            
            IntPtr newInstance = this.allocator.Alloc(size);
            CPyMarshal.Zero(newInstance, size);
            CPyMarshal.WriteUIntField(newInstance, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(newInstance, typeof(PyObject), "ob_type", typePtr);

            if (nItems > 0)
            {
                CPyMarshal.WriteUIntField(newInstance, typeof(PyVarObject), "ob_size", nItems);
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
            
            Py_TPFLAGS flags = (Py_TPFLAGS)CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), "tp_flags");
            if ((Int32)(flags & (Py_TPFLAGS.READY | Py_TPFLAGS.READYING)) != 0)
            {
                return 0;
            }
            flags |= Py_TPFLAGS.READYING;
            CPyMarshal.WriteIntField(typePtr, typeof(PyTypeObject), "tp_flags", (Int32)flags);
            
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
            this.InheritSubclassFlags(typePtr);
            this.InheritPtrField(typePtr, "tp_alloc");
            this.InheritPtrField(typePtr, "tp_new");
            this.InheritPtrField(typePtr, "tp_dealloc");
            this.InheritPtrField(typePtr, "tp_free");
            this.InheritPtrField(typePtr, "tp_doc");
            this.InheritPtrField(typePtr, "tp_call");
            this.InheritPtrField(typePtr, "tp_as_number");
            this.InheritPtrField(typePtr, "tp_as_sequence");
            this.InheritPtrField(typePtr, "tp_as_mapping");
            this.InheritPtrField(typePtr, "tp_as_buffer");
            this.InheritIntField(typePtr, "tp_basicsize");
            this.InheritIntField(typePtr, "tp_itemsize");

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
                    CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), "tp_dict", this.Store(typeDict));
                }
            }

            flags = (Py_TPFLAGS)CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), "tp_flags");
            flags |= Py_TPFLAGS.READY | Py_TPFLAGS.HAVE_CLASS;
            flags &= ~Py_TPFLAGS.READYING;
            CPyMarshal.WriteIntField(typePtr, typeof(PyTypeObject), "tp_flags", (Int32)flags);
            return 0;
        }

        public override IntPtr
        PyClass_New(IntPtr basesPtr, IntPtr dictPtr, IntPtr namePtr)
        {
            try
            {
                PythonTuple bases = new PythonTuple();
                if (basesPtr != IntPtr.Zero)
                {
                    bases = (PythonTuple)this.Retrieve(basesPtr);
                }
                return this.Store(OldClass.__new__(this.scratchContext, 
                    TypeCache.OldClass, (string)this.Retrieve(namePtr), bases, (PythonDictionary)this.Retrieve(dictPtr)));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
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
        
        public override void
        Fill_PyEllipsis_Type(IntPtr address)
        {
            // not quite trivial to autogenerate
            // (but surely there's a better way to get the Ellipsis object...)
            CPyMarshal.Zero(address, Marshal.SizeOf(typeof(PyTypeObject)));
            CPyMarshal.WriteIntField(address, typeof(PyTypeObject), "ob_refcnt", 1);
            object ellipsisType = PythonCalls.Call(Builtin.type, new object[] { PythonOps.Ellipsis });
            this.map.Associate(address, ellipsisType);
        }
        
        public override void
        Fill_PyNotImplemented_Type(IntPtr address)
        {
            // not quite trivial to autogenerate
            // (but surely there's a better way to get the NotImplemented object...)
            CPyMarshal.Zero(address, Marshal.SizeOf(typeof(PyTypeObject)));
            CPyMarshal.WriteIntField(address, typeof(PyTypeObject), "ob_refcnt", 1);
            object notImplementedType = PythonCalls.Call(Builtin.type, new object[] { PythonOps.NotImplemented });
            this.map.Associate(address, notImplementedType);
        }

        public override void
        Fill_PyBool_Type(IntPtr address)
        {
            // not quite trivial to autogenerate
            CPyMarshal.Zero(address, Marshal.SizeOf(typeof(PyTypeObject)));
            CPyMarshal.WriteIntField(address, typeof(PyTypeObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_base", this.PyInt_Type);
            this.map.Associate(address, TypeCache.Boolean);
        }

        public override void
        Fill_PyString_Type(IntPtr address)
        {
            // not quite trivial to autogenerate
            CPyMarshal.Zero(address, Marshal.SizeOf(typeof(PyTypeObject)));
            CPyMarshal.WriteIntField(address, typeof(PyTypeObject), "ob_refcnt", 1);
            CPyMarshal.WriteIntField(address, typeof(PyTypeObject), "tp_basicsize", Marshal.SizeOf(typeof(PyStringObject)) - 1);
            CPyMarshal.WriteIntField(address, typeof(PyTypeObject), "tp_itemsize", 1);
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_str", this.GetAddress("IC_PyString_Str"));
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_repr", this.GetAddress("PyObject_Repr"));

            uint sqSize = (uint)Marshal.SizeOf(typeof(PySequenceMethods));
            IntPtr sqPtr = this.allocator.Alloc(sqSize);
            CPyMarshal.Zero(sqPtr, sqSize);
            CPyMarshal.WritePtrField(sqPtr, typeof(PySequenceMethods), "sq_concat", this.GetAddress("IC_PyString_Concat_Core"));
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_as_sequence", sqPtr);

            uint bfSize = (uint)Marshal.SizeOf(typeof(PyBufferProcs));
            IntPtr bfPtr = this.allocator.Alloc(bfSize);
            CPyMarshal.Zero(bfPtr, bfSize);
            CPyMarshal.WritePtrField(bfPtr, typeof(PyBufferProcs), "bf_getreadbuffer", this.GetAddress("IC_str_getreadbuffer"));
            CPyMarshal.WritePtrField(bfPtr, typeof(PyBufferProcs), "bf_getwritebuffer", this.GetAddress("IC_str_getwritebuffer"));
            CPyMarshal.WritePtrField(bfPtr, typeof(PyBufferProcs), "bf_getsegcount", this.GetAddress("IC_str_getsegcount"));
            CPyMarshal.WritePtrField(bfPtr, typeof(PyBufferProcs), "bf_getcharbuffer", this.GetAddress("IC_str_getreadbuffer"));
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_as_buffer", bfPtr);
            
            CPyMarshal.WriteIntField(address, typeof(PyTypeObject), "tp_flags", (Int32)Py_TPFLAGS.HAVE_GETCHARBUFFER);

            this.map.Associate(address, TypeCache.String);
        }

        public override void
        Fill_PyFile_Type(IntPtr address)
        {
            // not worth autogenerating
            // we're using the cpy file type by default, with methods patched in C
            // to redirect into C# when ipy files turn up
            CPyMarshal.WriteIntField(address, typeof(PyTypeObject), "ob_refcnt", 1);
            this.map.Associate(address, TypeCache.PythonFile);
        }

        private void
        AddNumberMethodsWithoutIndex(IntPtr typePtr)
        {
            uint nmSize = (uint)Marshal.SizeOf(typeof(PyNumberMethods));
            IntPtr nmPtr = this.allocator.Alloc(nmSize);
            CPyMarshal.Zero(nmPtr, nmSize);

            CPyMarshal.WritePtrField(nmPtr, typeof(PyNumberMethods), "nb_int", this.GetAddress("PyNumber_Int"));
            CPyMarshal.WritePtrField(nmPtr, typeof(PyNumberMethods), "nb_long", this.GetAddress("PyNumber_Long"));
            CPyMarshal.WritePtrField(nmPtr, typeof(PyNumberMethods), "nb_float", this.GetAddress("PyNumber_Float"));
            CPyMarshal.WritePtrField(nmPtr, typeof(PyNumberMethods), "nb_multiply", this.GetAddress("PyNumber_Multiply"));

            CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), "tp_as_number", nmPtr);
        }
        
        private void
        AddNumberMethodsWithIndex(IntPtr typePtr)
        {
            this.AddNumberMethodsWithoutIndex(typePtr);
            IntPtr nmPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_as_number");
            CPyMarshal.WritePtrField(nmPtr, typeof(PyNumberMethods), "nb_index", this.GetAddress("PyNumber_Index"));
            
            Py_TPFLAGS flags = (Py_TPFLAGS)CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), "tp_flags");
            flags |= Py_TPFLAGS.HAVE_INDEX;
            CPyMarshal.WriteIntField(typePtr, typeof(PyTypeObject), "tp_flags", (Int32)flags);
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
            this.PyType_Ready(this.PyNone_Type);
            this.PyType_Ready(this.PySlice_Type);
            this.PyType_Ready(this.PyEllipsis_Type);
            this.PyType_Ready(this.PyNotImplemented_Type);
            this.PyType_Ready(this.PySeqIter_Type);
            this.PyType_Ready(this.PyCell_Type);
            this.PyType_Ready(this.PyMethod_Type);
            this.PyType_Ready(this.PyFunction_Type);
            this.PyType_Ready(this.PyClass_Type);
            this.PyType_Ready(this.PyInstance_Type);

            this.actualisableTypes[this.PyType_Type] = new ActualiseDelegate(this.ActualiseType);
            
            // now, let's corrupt the mapping in a useful way...
            this.cFileClass = this.GenerateClass(this.PyFile_Type);
            Builtin.setattr(this.scratchContext, this.cFileClass, "__name__", "cpy_file");
            this.actualisableTypes[this.PyFile_Type] = new ActualiseDelegate(this.ActualiseArbitraryObject);
            this.map.Associate(this.PyFile_Type, this.cFileClass);
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
                
        private void
        InheritIntField(IntPtr typePtr, string name)
        {
            int fieldVal = CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), name);
            if (fieldVal == 0)
            {
                IntPtr basePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_base");
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
            Py_TPFLAGS flags = (Py_TPFLAGS)CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), "tp_flags");
            
            if (this.PyType_IsSubtype(typePtr, this.PyInt_Type) != 0) { flags |= Py_TPFLAGS.INT_SUBCLASS; }
            if (this.PyType_IsSubtype(typePtr, this.PyLong_Type) != 0) { flags |= Py_TPFLAGS.LONG_SUBCLASS; }
            if (this.PyType_IsSubtype(typePtr, this.PyList_Type) != 0) { flags |= Py_TPFLAGS.LIST_SUBCLASS; }
            if (this.PyType_IsSubtype(typePtr, this.PyTuple_Type) != 0) { flags |= Py_TPFLAGS.TUPLE_SUBCLASS; }
            if (this.PyType_IsSubtype(typePtr, this.PyString_Type) != 0) { flags |= Py_TPFLAGS.STRING_SUBCLASS; }
            if (this.PyType_IsSubtype(typePtr, this.PyDict_Type) != 0) { flags |= Py_TPFLAGS.DICT_SUBCLASS; }
            if (this.PyType_IsSubtype(typePtr, this.PyType_Type) != 0) { flags |= Py_TPFLAGS.TYPE_SUBCLASS; }
            // TODO: PyExc_BaseException is tedious
            
            CPyMarshal.WriteIntField(typePtr, typeof(PyTypeObject), "tp_flags", (Int32)flags);
        }

        private IntPtr
        StoreTyped(PythonType _type)
        {
            uint typeSize = (uint)Marshal.SizeOf(typeof(PyTypeObject));
            IntPtr typePtr = this.allocator.Alloc(typeSize);
            CPyMarshal.Zero(typePtr, typeSize);
            
            CPyMarshal.WriteIntField(typePtr, typeof(PyTypeObject), "ob_refcnt", 2);

            object ob_type = PythonCalls.Call(this.scratchContext, Builtin.type, new object[] { _type });
            CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), "ob_type", this.Store(ob_type));
            
            string tp_name = (string)_type.__getattribute__(this.scratchContext, "__name__");
            CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), "tp_name", this.Store(tp_name));
            
            PythonTuple tp_bases = (PythonTuple)_type.__getattribute__(this.scratchContext, "__bases__");
            object tp_base = tp_bases[0];
            CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), "tp_base", this.Store(tp_base));
            if (tp_bases.__len__() > 1)
            {
                CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), "tp_bases", this.Store(tp_bases));
            }

            this.scratchModule.__dict__["_ironclad_bases"] = tp_bases;
            this.scratchModule.__dict__["_ironclad_metaclass"] = ob_type;
            this.ExecInModule(CodeSnippets.CLASS_STUB_CODE, this.scratchModule);
            this.classStubs[typePtr] = this.scratchModule.__dict__["_ironclad_class_stub"];

            this.actualisableTypes[typePtr] = new ActualiseDelegate(this.ActualiseArbitraryObject);
            this.map.Associate(typePtr, _type);
            this.PyType_Ready(typePtr);
            return typePtr;
        }
        
        private IntPtr
        StoreTyped(OldClass cls)
        {
            uint size = (uint)Marshal.SizeOf(typeof(PyClassObject));
            IntPtr ptr = this.allocator.Alloc(size);
            CPyMarshal.Zero(ptr, size);
            
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 2); // leak classes deliberately
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.PyClass_Type);
            
            CPyMarshal.WritePtrField(ptr, typeof(PyClassObject), "cl_bases", 
                this.Store(Builtin.getattr(this.scratchContext, cls, "__bases__")));
            CPyMarshal.WritePtrField(ptr, typeof(PyClassObject), "cl_dict", 
                this.Store(Builtin.getattr(this.scratchContext, cls, "__dict__")));
            CPyMarshal.WritePtrField(ptr, typeof(PyClassObject), "cl_name", 
                this.Store(Builtin.getattr(this.scratchContext, cls, "__name__")));
            
            this.map.Associate(ptr, cls);
            return ptr;
        }
        
        private IntPtr
        StoreTyped(OldInstance inst)
        {
            uint size = (uint)Marshal.SizeOf(typeof(PyInstanceObject));
            IntPtr ptr = this.allocator.Alloc(size);
            CPyMarshal.Zero(ptr, size);
            
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.PyInstance_Type);

            CPyMarshal.WritePtrField(ptr, typeof(PyInstanceObject), "in_class", 
                this.Store(Builtin.getattr(this.scratchContext, inst, "__class__")));
            CPyMarshal.WritePtrField(ptr, typeof(PyInstanceObject), "in_dict", 
                this.Store(Builtin.getattr(this.scratchContext, inst, "__dict__")));
            
            this.map.Associate(ptr, inst);
            return ptr;
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
            IntPtr typePtr = CPyMarshal.ReadPtrField(ptr, typeof(PyObject), "ob_type");
            PythonType type_ = (PythonType)this.Retrieve(typePtr);
            
            object[] args = new object[]{};
            if (Builtin.issubclass(this.scratchContext, type_, TypeCache.Int32))
            {
                args = new object[] { CPyMarshal.ReadIntField(ptr, typeof(PyIntObject), "ob_ival") };
            }
            if (Builtin.issubclass(this.scratchContext, type_, TypeCache.Double))
            {
                args = new object[] { CPyMarshal.ReadDoubleField(ptr, typeof(PyFloatObject), "ob_fval") };
            }
            if (Builtin.issubclass(this.scratchContext, type_, TypeCache.String))
            {
                args = new object[] { this.ReadPyString(ptr) };
            }
            if (Builtin.issubclass(this.scratchContext, type_, TypeCache.PythonType))
            {
                string name = CPyMarshal.ReadCStringField(ptr, typeof(PyTypeObject), "tp_name");
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
