using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Operations;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;

using Ironclad.Structs;

namespace Ironclad
{

    public enum UnmanagedDataMarker
    {
        PyStringObject,
        PyTupleObject,
        PyListObject,
        None,
    }

    public class BadRefCountException : Exception
    {
        public BadRefCountException(string message): base(message)
        {
        }
    }


    public partial class Python25Mapper : PythonMapper
    {
        private ScriptEngine engine;
        private StubReference stub;
        private PydImporter importer;
        private IAllocator allocator;
        private InterestingPtrMap map = new InterestingPtrMap();

        private PythonModule scratchModule;        
        private PythonModule dispatcherModule;
        private object dispatcherClass;

        private StupidSet ptrsForCleanup = new StupidSet();
        
        private List<IntPtr> tempObjects = new List<IntPtr>();
        private Dictionary<IntPtr, IntPtr> FILEs = new Dictionary<IntPtr, IntPtr>();
        private Dictionary<IntPtr, List> listsBeingActualised = new Dictionary<IntPtr, List>();
        private object _lastException = null;
        
        public Python25Mapper() : this(null, ScriptRuntime.Create().GetEngine("py"), new HGlobalAllocator())
        {
        }

        public Python25Mapper(string stubPath) : this(stubPath, ScriptRuntime.Create().GetEngine("py"), new HGlobalAllocator())
        {
        }

        public Python25Mapper(IAllocator alloc) : this(null, ScriptRuntime.Create().GetEngine("py"), alloc)
        {
        }

        public Python25Mapper(string stubPath, ScriptEngine inEngine, IAllocator alloc)
        {
            this.engine = inEngine;
            this.allocator = alloc;
            this.CreateDispatcherModule();
            this.CreateScratchModule();
            if (stubPath != null)
            {
                this.stub = new StubReference(stubPath);
                this.stub.Init(new AddressGetterDelegate(this.GetAddress), new DataSetterDelegate(this.SetData));
                this.importer = new PydImporter();
            }
        }
        
        public void Dispose()
        {
            foreach (object ptr in this.ptrsForCleanup.ElementsArray)
            {
                // My understanding is that I really ought to Retrieve each object and
                // call GC.SuppressFinalize, to prevent their __del__s attempting to re-free
                // their memory. However, we haven't been able to detect any change in
                // behaviour when we try to do that, so... er... we don't do it.
                IntPtr typePtr = CPyMarshal.ReadPtrField((IntPtr)ptr, typeof(PyObject), "ob_type");
                CPython_destructor_Delegate dgt = (CPython_destructor_Delegate)
                    CPyMarshal.ReadFunctionPtrField(
                        typePtr, typeof(PyTypeObject), "tp_dealloc", typeof(CPython_destructor_Delegate));
                dgt((IntPtr)ptr);
            }
            this.allocator.FreeAll();
            foreach (IntPtr FILE in this.FILEs.Values)
            {
                Unmanaged.fclose(FILE);
            }
            if (this.stub != null)
            {
                this.importer.Dispose();
                this.stub.Dispose();
            }
        }
        
        public ScriptEngine
        Engine
        {
            get
            {
                return this.engine;
            }
        }
        
        public IntPtr 
        Store(object obj)
        {
            if (obj != null && obj.GetType() == typeof(UnmanagedDataMarker))
            {
                throw new ArgumentTypeException("UnmanagedDataMarkers should not be stored by clients.");
            }
            if (obj == null)
            {
                this.IncRef(this._Py_NoneStruct);
                return this._Py_NoneStruct;
            }
            if (this.map.HasObj(obj))
            {
                IntPtr ptr = this.map.GetPtr(obj);
                this.IncRef(ptr);
                return ptr;
            }
            return this.StoreDispatch(obj);
        }
        
        
        private IntPtr
        StoreObject(object obj)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", 1);
            CPyMarshal.WritePtrField(ptr, typeof(PyObject), "ob_type", this.PyBaseObject_Type);
            this.map.Associate(ptr, obj);
            return ptr;
        }
        
        
        public void
        StoreUnmanagedInstance(IntPtr ptr, object obj)
        {
            this.map.WeakAssociate(ptr, obj);
            this.ptrsForCleanup.Add(ptr);
        }
        
        
        public object 
        Retrieve(IntPtr ptr)
        {
            if (this.map.HasPtr(ptr))
            {
                object possibleMarker = this.map.GetObj(ptr);
                if (possibleMarker.GetType() == typeof(UnmanagedDataMarker))
                {
                    UnmanagedDataMarker marker = (UnmanagedDataMarker)possibleMarker;
                    switch (marker)
                    {
                        case UnmanagedDataMarker.None:
                            return null;

                        case UnmanagedDataMarker.PyStringObject:
                            this.ActualiseString(ptr);
                            break;

                        case UnmanagedDataMarker.PyTupleObject:
                            this.ActualiseTuple(ptr);
                            break;

                        case UnmanagedDataMarker.PyListObject:
                            ActualiseList(ptr);
                            break;

                        default:
                            throw new Exception("Found impossible data in pointer map");
                    }
                }
            }
            else if (ptr != IntPtr.Zero)
            {
                IntPtr typePtr = CPyMarshal.ReadPtrField(ptr, typeof(PyTypeObject), "ob_type");
                if (typePtr == this.PyType_Type)
                {
                    this.GenerateClass(ptr);
                }
            }
            return this.map.GetObj(ptr);
        }
        
        public int 
        RefCount(IntPtr ptr)
        {
            if (this.map.HasPtr(ptr))
            {
                return CPyMarshal.ReadIntField(ptr, typeof(PyObject), "ob_refcnt");
            }
            else
            {
                throw new KeyNotFoundException(String.Format(
                    "RefCount: missing key in pointer map: {0}", ptr));
            }
        }
        
        public void 
        IncRef(IntPtr ptr)
        {
            if (this.map.HasPtr(ptr))
            {
                int count = CPyMarshal.ReadIntField(ptr, typeof(PyObject), "ob_refcnt");
                CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", count + 1);
            }
            else
            {
                throw new KeyNotFoundException(String.Format(
                    "IncRef: missing key in pointer map: {0}", ptr));
            }
        }
        
        public void 
        DecRef(IntPtr ptr)
        {
            if (this.map.HasPtr(ptr))
            {
                int count = CPyMarshal.ReadIntField(ptr, typeof(PyObject), "ob_refcnt");
                if (count == 0)
                {
                    throw new BadRefCountException("Trying to DecRef an object with ref count 0");
                }
                
                if (count == 1)
                {
                    IntPtr typePtr = CPyMarshal.ReadPtrField(ptr, typeof(PyObject), "ob_type");

                    if (typePtr != IntPtr.Zero)
                    {
                        if (CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_dealloc") != IntPtr.Zero)
                        {
                            CPython_destructor_Delegate deallocDgt = (CPython_destructor_Delegate)
                                CPyMarshal.ReadFunctionPtrField(
                                    typePtr, typeof(PyTypeObject), "tp_dealloc", typeof(CPython_destructor_Delegate));
                            deallocDgt(ptr);
                            return;
                        }
                    }
                    // TODO: remove this get-out-of-jail-free, and ensure that 
                    // all the types I create actually have dealloc functions
                    this.PyObject_Free(ptr);
                }
                else
                {
                    CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", count - 1);
                }
            }
            else
            {
                throw new KeyNotFoundException(String.Format(
                    "DecRef: missing key in pointer map: {0}", ptr));
            }
        }
        
        public void 
        Strengthen(object obj)
        {
            this.map.Strengthen(obj);
        }
        
        public void 
        Weaken(object obj)
        {
            this.map.Weaken(obj);
        }
        
        public void 
        ReapStrongRefs()
        {
            object[] refs = this.map.GetStrongRefs();
            foreach (object obj in refs)
            {
                IntPtr ptr = this.map.GetPtr(obj);
                if (this.RefCount(ptr) < 2)
                {
                    this.map.Weaken(obj);
                }
            }
        }
        
        public override void 
        PyObject_Free(IntPtr ptr)
        {
            if (this.FILEs.ContainsKey(ptr))
            {
                Unmanaged.fclose(this.FILEs[ptr]);
                this.FILEs.Remove(ptr);
            }
            this.ptrsForCleanup.RemoveIfPresent(ptr);
            this.map.Release(ptr);
            this.allocator.Free(ptr);
        }

        public void RememberTempObject(IntPtr ptr)
        {
            this.tempObjects.Add(ptr);
        }

        public void FreeTemps()
        {
            foreach (IntPtr ptr in this.tempObjects)
            {
                this.DecRef(ptr);
            }
            this.tempObjects.Clear();
        }
        
        public object LastException
        {
            get
            {
                return this._lastException;
            }
            set
            {
                this._lastException = value;
            }
        }
        
        public override void
        PyErr_SetString(IntPtr excTypePtr, string message)
        {
            if (excTypePtr == IntPtr.Zero)
            {
                this._lastException = new Exception(message);
            }
            else
            {
                object excType = this.Retrieve(excTypePtr);
                this._lastException = PythonCalls.Call(excType, new object[1]{ message });
            }
        }
        
        
        public IntPtr 
        GetMethodFP(string name)
        {
            Delegate result;
            if (this.dgtMap.TryGetValue(name, out result))
            {
                return Marshal.GetFunctionPointerForDelegate(result);
            }

            switch (name)
            {
                case "PyBaseObject_Dealloc":
                    this.dgtMap[name] = new CPython_destructor_Delegate(this.PyBaseObject_Dealloc);
                    break;
                case "PyTuple_Dealloc":
                    this.dgtMap[name] = new CPython_destructor_Delegate(this.PyTuple_Dealloc);
                    break;
                case "PyList_Dealloc":
                    this.dgtMap[name] = new CPython_destructor_Delegate(this.PyList_Dealloc);
                    break;
                
                default:
                    break;
            }
            return Marshal.GetFunctionPointerForDelegate(this.dgtMap[name]);
        }
        
        
        public override int
        PyCallable_Check(IntPtr objPtr)
        {
            if (Builtin.callable(this.Retrieve(objPtr)))
            {
                return 1;
            }
            return 0;
        }
        
        
        public override void
        Fill__Py_NoneStruct(IntPtr address)
        {
            PyObject none = new PyObject();
            none.ob_refcnt = 1;
            none.ob_type = IntPtr.Zero;
            Marshal.StructureToPtr(none, address, false);
            this.map.Associate(address, UnmanagedDataMarker.None);
        }
        
    }

}
