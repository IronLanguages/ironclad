using System;
using System.Collections;

using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Microsoft.Scripting;

using Ironclad.Structs;

namespace Ironclad
{

    public partial class Python25Mapper: Python25Api
    {
        public override IntPtr
        _PyObject_New(IntPtr typePtr)
        {
            int ob_size = CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), "ob_size");
            IntPtr objPtr = this.allocator.Alloc(ob_size);
            return this.PyObject_Init(objPtr, typePtr);
        }
        
        public override IntPtr
        PyObject_Init(IntPtr objPtr, IntPtr typePtr)
        {
            CPyMarshal.WriteIntField(objPtr, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(objPtr, typeof(PyObject), "ob_type", typePtr);
            return objPtr;
        }
        
        public int PyBaseObject_Init(IntPtr self, IntPtr args, IntPtr kwargs)
        {
            return 0;
        }
        
        public virtual void 
        PyBaseObject_Dealloc(IntPtr objPtr)
        {
            IntPtr objType = CPyMarshal.ReadPtrField(objPtr, typeof(PyObject), "ob_type");
            PyObject_Free_Delegate freeDgt = (PyObject_Free_Delegate)
                CPyMarshal.ReadFunctionPtrField(
                    objType, typeof(PyTypeObject), "tp_free", typeof(PyObject_Free_Delegate));
            freeDgt(objPtr);
        }
        
        public override void 
        PyObject_Free(IntPtr ptr)
        {
            this.Unmap(ptr);
            this.allocator.Free(ptr);
        }
        
        
        public override int
        PyObject_Compare(IntPtr ptr1, IntPtr ptr2)
        {
            return Builtin.cmp(this.scratchContext, this.Retrieve(ptr1), this.Retrieve(ptr2));
        }
        
        
        public override int
        PyObject_RichCompareBool(IntPtr ptr1, IntPtr ptr2, int opid)
        {
            try
            {
                bool result = true;
                CMP op = (CMP)opid;
                switch (op)
                {
                    case CMP.Py_LT:
                        result = (bool)PythonOperator.lt(this.scratchContext, this.Retrieve(ptr1), this.Retrieve(ptr2));
                        break;
                    case CMP.Py_LE:
                        result = (bool)PythonOperator.le(this.scratchContext, this.Retrieve(ptr1), this.Retrieve(ptr2));
                        break;
                    case CMP.Py_EQ:
                        result = (bool)PythonOperator.eq(this.scratchContext, this.Retrieve(ptr1), this.Retrieve(ptr2));
                        break;
                    case CMP.Py_NE:
                        result = (bool)PythonOperator.ne(this.scratchContext, this.Retrieve(ptr1), this.Retrieve(ptr2));
                        break;
                    case CMP.Py_GT:
                        result = (bool)PythonOperator.gt(this.scratchContext, this.Retrieve(ptr1), this.Retrieve(ptr2));
                        break;
                    case CMP.Py_GE:
                        result = (bool)PythonOperator.ge(this.scratchContext, this.Retrieve(ptr1), this.Retrieve(ptr2));
                        break;
                }
                if (result)
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

            object result = null;
            if (kwargsPtr == IntPtr.Zero)
            {
               result = PythonCalls.Call(obj, argsArray);
            }
            else
            {
                IAttributesCollection kwargs = (IAttributesCollection)this.Retrieve(kwargsPtr);
                result = PythonCalls.CallWithKeywordArgs(this.scratchContext, obj, argsArray, kwargs);
            }
            return this.Store(result);
        }
        
        public override int
        PyObject_IsInstance(IntPtr instPtr, IntPtr clsPtr)
        {
            try
            {
                object inst = this.Retrieve(instPtr);
                object cls = this.Retrieve(clsPtr);
                if (Builtin.isinstance(inst, cls))
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
        
        
        public override int
        PyObject_Size(IntPtr objPtr)
        {
            try
            {
                int length = PythonOps.Length(this.Retrieve(objPtr));
                return length;
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
