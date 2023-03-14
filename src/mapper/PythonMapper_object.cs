using System;
using System.Collections;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Microsoft.Scripting;
using Microsoft.Scripting.Runtime;

using Ironclad.Structs;

namespace Ironclad
{

    public partial class PythonMapper: PythonApi
    {
        public override IntPtr
        _PyObject_New(IntPtr typePtr)
        {
            var tp_basicsize = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_basicsize));
            IntPtr objPtr = this.allocator.Alloc(tp_basicsize);
            CPyMarshal.Zero(objPtr, tp_basicsize);
            return this.PyObject_Init(objPtr, typePtr);
        }
        
        public override IntPtr
        _PyObject_NewVar(IntPtr typePtr, nint nitems)
        {
            nint tp_basicsize = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_basicsize));
            nint tp_itemsize = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), nameof(PyTypeObject.tp_itemsize));
            nint size = tp_basicsize + nitems * tp_itemsize;
            IntPtr objPtr = this.allocator.Alloc(size);
            CPyMarshal.Zero(objPtr, size);
            return this.PyObject_Init(objPtr, typePtr);
        }
        
        public override IntPtr
        PyObject_Init(IntPtr objPtr, IntPtr typePtr)
        {
            CPyMarshal.WritePtrField(objPtr, typeof(PyObject), nameof(PyObject.ob_refcnt), 1);
            CPyMarshal.WritePtrField(objPtr, typeof(PyObject), nameof(PyObject.ob_type), typePtr);
            return objPtr;
        }
        
        public override int 
        IC_PyBaseObject_Init(IntPtr self, IntPtr args, IntPtr kwargs)
        {
            return 0;
        }
        
        public override void 
        IC_PyBaseObject_Dealloc(IntPtr objPtr)
        {
            IntPtr objType = CPyMarshal.ReadPtrField(objPtr, typeof(PyObject), nameof(PyObject.ob_type));
            dgt_void_ptr freeDgt = CPyMarshal.ReadFunctionPtrField<dgt_void_ptr>(objType, typeof(PyTypeObject), nameof(PyTypeObject.tp_free));
            freeDgt(objPtr);
        }
        
        public override void 
        PyObject_Free(IntPtr ptr)
        {
            this.Unmap(ptr);
            this.allocator.Free(ptr);
        }

        private object
        RichCompare(IntPtr ptr1, IntPtr ptr2, int opid)
        {
            object objResult = true;
            CMP op = (CMP)opid;
            switch (op)
            {
                case CMP.Py_LT:
                    objResult = PythonOperator.lt(this.scratchContext, this.Retrieve(ptr1), this.Retrieve(ptr2));
                    break;
                case CMP.Py_LE:
                    objResult = PythonOperator.le(this.scratchContext, this.Retrieve(ptr1), this.Retrieve(ptr2));
                    break;
                case CMP.Py_EQ:
                    objResult = PythonOperator.eq(this.scratchContext, this.Retrieve(ptr1), this.Retrieve(ptr2));
                    break;
                case CMP.Py_NE:
                    objResult = PythonOperator.ne(this.scratchContext, this.Retrieve(ptr1), this.Retrieve(ptr2));
                    break;
                case CMP.Py_GT:
                    objResult = PythonOperator.gt(this.scratchContext, this.Retrieve(ptr1), this.Retrieve(ptr2));
                    break;
                case CMP.Py_GE:
                    objResult = PythonOperator.ge(this.scratchContext, this.Retrieve(ptr1), this.Retrieve(ptr2));
                    break;
            }
            return objResult;
        }
        
        public override int
        PyObject_RichCompareBool(IntPtr ptr1, IntPtr ptr2, int opid)
        {
            try
            {
                if (Converter.ConvertToBoolean(this.RichCompare(ptr1, ptr2, opid)))
                {
                    return 1;
                }
                return 0;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }

        public override IntPtr
        PyObject_RichCompare(IntPtr ptr1, IntPtr ptr2, int opid)
        {
            try
            {
                return this.Store((this.RichCompare(ptr1, ptr2, opid)));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        public override int
        PyCallable_Check(IntPtr objPtr)
        {
            if (Builtin.callable(this.scratchContext, this.Retrieve(objPtr)))
            {
                return 1;
            }
            return 0;
        }
        
        public override IntPtr
        PyObject_Call(IntPtr objPtr, IntPtr argsPtr, IntPtr kwargsPtr)
        {
            try
            {
                object obj = this.Retrieve(objPtr);

                object[] argsArray = null;

                if (argsPtr == IntPtr.Zero)
                {
                    argsArray = new object[0];
                }
                else
                {
                    ICollection args = (ICollection)this.Retrieve(argsPtr);
                    argsArray = new object[args.Count];
                    args.CopyTo(argsArray, 0);
                }

                PythonDictionary builtins = this.GetModule("builtins").Get__dict__();
                if (obj == builtins["__import__"])
                {
                    // I really, really wish that Pyrex used the C API for importing things,
                    // instead of PyObject_Call __import__. However, it doesn't, so I have to 
                    // do this.
                    // This is only tested in functionalitytest -- if h5's pyd submodules each 
                    // have their own copy of _sync, this bit is broken.
                    if (kwargsPtr != IntPtr.Zero)
                    {
                        throw new NotImplementedException("Someone tried to PyObject_Call __import__ with non-null kwargs.");
                    }
                    return this.DoFoulImportHack(argsArray);
                }

                object result = null;
                if (kwargsPtr == IntPtr.Zero)
                {
                   result = PythonCalls.Call(obj, argsArray);
                }
                else
                {
                    PythonDictionary kwargs = (PythonDictionary)this.Retrieve(kwargsPtr);
                    result = PythonCalls.CallWithKeywordArgs(this.scratchContext, obj, argsArray, kwargs);
                }
                
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
        
        private IntPtr DoFoulImportHack(object[] argsArray)
        {
            PythonDictionary dest = (PythonDictionary)argsArray[1];
            string tryimport = (string)argsArray[0];
            string __name__ = (string)dest["__name__"];
            
            object module = null;
            while (module == null)
            {
                try
                {
                    module = this.Import(tryimport);
                }
                catch
                {
                    int lastDot = __name__.LastIndexOf('.');
                    tryimport = String.Format("{0}{1}", __name__.Substring(0, lastDot + 1), tryimport); 
                    __name__ = __name__.Substring(0, lastDot);
                }
            }
            
            ICollection fromList = (ICollection)argsArray[3];
            foreach (object name_ in fromList)
            {
                string name = (string)name_;
                dest[name] = Builtin.getattr(this.scratchContext, module, name);
            }
            return this.Store(module);
        
        }
        
        
        public override int
        PyObject_IsInstance(IntPtr instPtr, IntPtr clsPtr)
        {
            try
            {
                object inst = this.Retrieve(instPtr);
                object cls = this.Retrieve(clsPtr);
                if (InappropriateReflection.IsInstance(this.scratchContext, inst, cls))
                {
                    return 1;
                }
                return 0;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }
        
        public override int
        PyObject_IsSubclass(IntPtr derivedPtr, IntPtr clsPtr)
        {
            try
            {
                object derived = this.Retrieve(derivedPtr);
                object cls = this.Retrieve(clsPtr);
                var res = Builtin.issubclass(this.scratchContext, derived, cls);
                LightExceptions.CheckAndThrow(res);
                return (bool)res ? 1 : 0;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }

        public override IntPtr
        PyObject_GetAttrString(IntPtr objPtr, string name)
        {
            object obj = this.Retrieve(objPtr);
            if (Builtin.hasattr(this.scratchContext, obj, name))
            {
                return this.Store(Builtin.getattr(this.scratchContext, obj, name));
            }
            return IntPtr.Zero;
        }

        public override IntPtr
        PyObject_GetAttr(IntPtr objPtr, IntPtr namePtr)
        {
            string name = (string)this.Retrieve(namePtr);
            return this.PyObject_GetAttrString(objPtr, name);
        }

        public override int
        PyObject_HasAttrString(IntPtr objPtr, string name)
        {
            object obj = this.Retrieve(objPtr);
            if (Builtin.hasattr(this.scratchContext, obj, name))
            {
                return 1;
            }
            return 0;
        }

        public override int
        PyObject_HasAttr(IntPtr objPtr, IntPtr namePtr)
        {
            string name = (string)this.Retrieve(namePtr);
            return this.PyObject_HasAttrString(objPtr, name);
        }

        public override int
        PyObject_SetAttrString(IntPtr objPtr, string name, IntPtr valuePtr)
        {
            object obj = this.Retrieve(objPtr);
            object value = this.Retrieve(valuePtr);
            try
            {
                Builtin.setattr(this.scratchContext, obj, name, value);
                return 0;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }

        public override int
        PyObject_SetAttr(IntPtr objPtr, IntPtr namePtr, IntPtr valuePtr)
        {
            string name = (string)this.Retrieve(namePtr);
            return this.PyObject_SetAttrString(objPtr, name, valuePtr);
        }

        public override int
        PyObject_SetItem(IntPtr objPtr, IntPtr keyPtr, IntPtr valuePtr)
        {
            try
            {
                PythonOperator.setitem(this.scratchContext, this.Retrieve(objPtr), this.Retrieve(keyPtr), this.Retrieve(valuePtr));
                return 0;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }
        
        public override int
        PyObject_DelItemString(IntPtr objPtr, string key)
        {
            try
            {
                PythonOperator.delitem(this.scratchContext, this.Retrieve(objPtr), key);
                return 0;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }

        public override int
        PyObject_IsTrue(IntPtr objPtr)
        {
            try
            {
                if (Converter.ConvertToBoolean(this.Retrieve(objPtr)))
                {
                    return 1;
                }
                return 0;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }
        
        
        public override nint
        PyObject_Size(IntPtr objPtr)
        {
            try
            {
                return (int)PythonOps.Length(this.Retrieve(objPtr));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }
        
        public override int
        PyObject_Hash(IntPtr objPtr)
        {
            try
            {
                return PythonOps.Hash(this.scratchContext, this.Retrieve(objPtr));
            }
            catch (Exception e)
            {
                this.LastException = e;
                return -1;
            }
        }
        

        public override IntPtr
        PyObject_Str(IntPtr objPtr)
        {
            try
            {
                object obj = this.Retrieve(objPtr);
                if (obj is string)
                {
                    return this.Store(obj);
                }
                return this.Store(PythonCalls.Call(Builtin.str, new object[] { obj }));
                
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        PyObject_Repr(IntPtr objPtr)
        {
            try
            {
                object obj = this.Retrieve(objPtr);
                return this.Store(Builtin.repr(this.scratchContext, obj));

            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
        
    }
}
