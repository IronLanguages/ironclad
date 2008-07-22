using System;
using System.Collections;

using IronPython.Runtime;
using IronPython.Runtime.Calls;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Microsoft.Scripting;

using Ironclad.Structs;

namespace Ironclad
{

    public partial class Python25Mapper: Python25Api
    {
        public override void
        Fill_PyBaseObject_Type(IntPtr address)
        {
            CPyMarshal.WriteIntField(address, typeof(PyTypeObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_init", this.GetAddress("PyBaseObject_Init"));
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_alloc", this.GetAddress("PyType_GenericAlloc"));
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_new", this.GetAddress("PyType_GenericNew"));
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_dealloc", this.GetAddress("PyBaseObject_Dealloc"));
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_free", this.GetAddress("PyObject_Free"));
            this.map.Associate(address, TypeCache.Object);
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
        
        public override IntPtr
        PyObject_Call(IntPtr objPtr, IntPtr argsPtr, IntPtr kwargsPtr)
        {
            // TODO ignore kwargsPtr for now
            object obj = this.Retrieve(objPtr);
            ICollection args = (ICollection)this.Retrieve(argsPtr);
            object[] argsArray = new object[args.Count];
            args.CopyTo(argsArray, 0);
            
            object result = PythonCalls.Call(obj, argsArray);
            IntPtr resultPtr = this.Store(result);
            return resultPtr;
        }
        
        public override IntPtr
        PyObject_Init(IntPtr objPtr, IntPtr typePtr)
        {
            object managedInstance = PythonCalls.Call(this.trivialObjectSubclass);
            Builtin.setattr(DefaultContext.Default, managedInstance, "_instancePtr", objPtr);
            Builtin.setattr(DefaultContext.Default, managedInstance, "__class__", this.Retrieve(typePtr));
            
            CPyMarshal.WriteIntField(objPtr, typeof(PyObject), "ob_refcnt", 2);
            CPyMarshal.WritePtrField(objPtr, typeof(PyObject), "ob_type", typePtr);
            this.map.WeakAssociate(objPtr, managedInstance);
            
            return objPtr;
        }
        
        public override IntPtr
        PyObject_GetAttrString(IntPtr objPtr, string name)
        {
            object obj = this.Retrieve(objPtr);
            if (Builtin.hasattr(DefaultContext.Default, obj, name))
            {
                return this.Store(Builtin.getattr(DefaultContext.Default, obj, name));
            }
            return IntPtr.Zero;
        }
        
        
        public override IntPtr
        PyObject_GetIter(IntPtr objPtr)
        {
            IEnumerable enumerable = this.Retrieve(objPtr) as IEnumerable;
            if (enumerable == null)
            {
                this.LastException = new ArgumentTypeException("PyObject_GetIter: object is not iterable");
                return IntPtr.Zero;
            }
            return this.Store(enumerable.GetEnumerator());
        }
        
        public override IntPtr
        PyIter_Next(IntPtr iterPtr)
        {
            IEnumerator enumerator = this.Retrieve(iterPtr) as IEnumerator;
            if (enumerator == null)
            {
                this.LastException = new ArgumentTypeException("PyIter_Next: object is not an iterator");
                return IntPtr.Zero;
            }
            try
            {
                bool notFinished = enumerator.MoveNext();
                if (notFinished)
                {
                    return this.Store(enumerator.Current);
                }
                return IntPtr.Zero;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
    }
}
