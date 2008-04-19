using System;
using System.Collections;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Calls;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Ironclad.Structs;

namespace Ironclad
{

    public partial class Python25Mapper: PythonMapper
    {
        public override void
        Fill_PyBaseObject_Type(IntPtr address)
        {
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_dealloc", this.GetMethodFP("PyBaseObject_Dealloc"));
            CPyMarshal.WritePtrField(address, typeof(PyTypeObject), "tp_free", this.GetAddress("PyObject_Free"));
            this.StoreUnmanagedData(address, TypeCache.Object);
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
            // ignore kwargsPtr for now
            ICallerContext context = this.GetPythonModule(
                this.engine.DefaultModule);
            object obj = this.Retrieve(objPtr);
            Tuple args = (Tuple)this.Retrieve(argsPtr);
            object[] argsArray = new object[args.Count];
            args.CopyTo(argsArray, 0);
            
            object result = Ops.CallWithContext(
                context, obj, argsArray);
            IntPtr resultPtr = this.Store(result);
            return resultPtr;
        }
        
        public override IntPtr
        PyObject_GetAttrString(IntPtr objPtr, string name)
        {
            object obj = this.Retrieve(objPtr);
            object attr = null;
            ICallerContext context = this.GetPythonModule(
                this.engine.DefaultModule);
            if (Ops.TryGetAttr(context, obj, SymbolTable.StringToId(name), out attr))
            {
                return this.Store(attr);
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