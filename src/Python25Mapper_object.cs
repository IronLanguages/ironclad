using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Calls;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Operations;

using Ironclad.Structs;

namespace Ironclad
{

    public partial class Python25Mapper: PythonMapper
    {
        public override void
        Fill_PyBaseObject_Type(IntPtr address)
        {
            IntPtr tp_deallocPtr = CPyMarshal.Offset(
                address, Marshal.OffsetOf(typeof(PyTypeObject), "tp_dealloc"));
            CPyMarshal.WritePtr(tp_deallocPtr, this.GetMethodFP("PyBaseObject_Dealloc"));

            IntPtr tp_freePtr = CPyMarshal.Offset(
                address, Marshal.OffsetOf(typeof(PyTypeObject), "tp_free"));
            CPyMarshal.WritePtr(tp_freePtr, this.GetMethodFP("Free"));
        }
        
        
        public virtual void 
        PyBaseObject_Dealloc(IntPtr objPtr)
        {
            IntPtr freeFPPtr = CPyMarshal.Offset(
                this.PyBaseObject_Type, Marshal.OffsetOf(typeof(PyTypeObject), "tp_free"));
            IntPtr freeFP = CPyMarshal.ReadPtr(freeFPPtr);
            CPython_destructor_Delegate freeDgt = (CPython_destructor_Delegate)Marshal.GetDelegateForFunctionPointer(
                freeFP, typeof(CPython_destructor_Delegate));
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
            return this.Store(result);
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
            this.LastException = new PythonNameErrorException(name);
            return IntPtr.Zero;
        }
        
        
    }
}