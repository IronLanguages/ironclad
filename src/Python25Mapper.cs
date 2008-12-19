using System;
using System.IO;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading;

using IronPython.Hosting;
using IronPython.Runtime;
using IronPython.Runtime.Operations;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Runtime;

using Ironclad.Structs;


namespace Ironclad
{
    public enum UnmanagedDataMarker
    {
        PyStringObject,
        PyTupleObject,
        PyListObject,
    }

    public class BadRefCountException : Exception
    {
        public BadRefCountException(string message): base(message)
        {
        }
    }

    public class CannotInterpretException : Exception
    {
        public CannotInterpretException(string message): base(message)
        {
        }
    }

    internal delegate void ActualiseDelegate(IntPtr typePtr);

    public partial class Python25Mapper : Python25Api, IDisposable
    {
        private PythonContext python;
        private StubReference stub;
        private PydImporter importer;
        private IAllocator allocator;

        private Scope scratchModule;
        private CodeContext scratchContext;
        
        private Scope dispatcherModule;
        private object dispatcherClass;
        private object kindaDictProxyClass;
        private Lock GIL;

        private bool alive = false;
        private bool appliedNumpyHack = false;
        
        private InterestingPtrMap map = new InterestingPtrMap();
        private Dictionary<IntPtr, ActualiseDelegate> actualisableTypes = new Dictionary<IntPtr, ActualiseDelegate>();
        private Dictionary<IntPtr, object> actualiseHelpers = new Dictionary<IntPtr, object>();
        private Dictionary<IntPtr, UnmanagedDataMarker> incompleteObjects = new Dictionary<IntPtr, UnmanagedDataMarker>();
        private Dictionary<IntPtr, List> listsBeingActualised = new Dictionary<IntPtr, List>();
        private Dictionary<string, IntPtr> internedStrings = new Dictionary<string, IntPtr>();
        private Dictionary<IntPtr, IntPtr> FILEs = new Dictionary<IntPtr, IntPtr>();
        private List<IntPtr> tempObjects = new List<IntPtr>();

        private LocalDataStoreSlot threadDictStore = Thread.AllocateDataSlot();
        private LocalDataStoreSlot threadLockStore = Thread.AllocateDataSlot();
        private LocalDataStoreSlot threadErrorStore = Thread.AllocateDataSlot();

        // one day, perhaps, this 'set' will be empty
        private StupidSet unknownNames = new StupidSet();

        // TODO: must be a better way to handle imports...
        private string importName = "";
        
        public Python25Mapper(CodeContext context)
        {
            this.Init(PythonContext.GetContext(context), null, new HGlobalAllocator());
        }
        
        public Python25Mapper(CodeContext context, string stubPath)
        {
            this.Init(PythonContext.GetContext(context), stubPath, new HGlobalAllocator());
        }
        
        public Python25Mapper(CodeContext context, IAllocator allocator)
        {
            this.Init(PythonContext.GetContext(context), null, allocator);
        }

        public Python25Mapper(PythonContext python, string stubPath, IAllocator allocator)
        {
            this.Init(python, stubPath, allocator);
        }

        private void Init(PythonContext inPython, string stubPath, IAllocator inAllocator)
        {
            this.GIL = new Lock();
            this.python = inPython;
            this.allocator = inAllocator;
            
            this.CreateScratchModule();
            this.CreateKindaDictProxy();
            this.CreateDispatcherModule();
            
            if (stubPath != null)
            {
                this.stub = new StubReference(stubPath);
                this.stub.Init(new AddressGetterDelegate(this.GetAddress), new DataSetterDelegate(this.SetData));
                this.ReadyBuiltinTypes();
                this.importer = new PydImporter();
                
                // TODO: work out why this line causes leakage
                this.ExecInModule(CodeSnippets.INSTALL_IMPORT_HOOK_CODE, this.scratchModule);
            }
            this.alive = true;
        }
        
        private void 
        DumpPtr(IntPtr ptr)
        {
            if (!this.allocator.Contains(ptr))
            {
                // we don't own this memory; not our problem.
                return;
            }
            try
            {
                // note: SuppressFinalize won't work on ipy objects, but is required for OpaquePyCObjects.
                GC.SuppressFinalize(this.Retrieve(ptr));
                IntPtr typePtr = CPyMarshal.ReadPtrField(ptr, typeof(PyObject), "ob_type");
                CPython_destructor_Delegate dealloc = (CPython_destructor_Delegate)
                    CPyMarshal.ReadFunctionPtrField(
                        typePtr, typeof(PyTypeObject), "tp_dealloc", typeof(CPython_destructor_Delegate));
                dealloc(ptr);
            }
            catch
            {
                // meh, we're probably deallocing things out of order. tough.
            }
        }
        
        protected virtual void 
        Dispose(bool disposing)
        {
            if (this.alive)
            {
                this.alive = false;
                this.StopDispatchingDeletes();
                this.map.MapOverBridgePtrs(new PtrFunc(this.DumpPtr));
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
        }
        
        public void 
        Dispose()
        {
            this.GIL.Acquire();
            try
            {
                GC.SuppressFinalize(this);
                this.Dispose(true);
            }
            finally
            {
                this.GIL.Release();
            }
        }

        public bool
        Alive
        {
            get { return this.alive; }
        }
        
        public int GCThreshold
        {
            get {
                return this.map.GCThreshold;
            }
            set {
                this.map.GCThreshold = value;
            }
        }
        
        public IntPtr 
        Store(object obj)
        {
            if (obj != null && obj.GetType() == typeof(UnmanagedDataMarker))
            {
                throw new ArgumentTypeException("UnmanagedDataMarkers should not be Store()d.");
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
                GC.KeepAlive(obj); // please test me, if you can work out how to
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
        StoreBridge(IntPtr ptr, object obj)
        {
            this.map.BridgeAssociate(ptr, obj);
        }
        
        
        public bool
        HasPtr(IntPtr ptr)
        {
            if (ptr == IntPtr.Zero)
            {
                return false;
            }
            if (ptr == this._Py_NoneStruct)
            {
                return true;
            }
            return (this.map.HasPtr(ptr) || this.incompleteObjects.ContainsKey(ptr));
        }
        

        private void
        AttemptToMap(IntPtr ptr)
        {
            if (this.HasPtr(ptr))
            {
                return;
            }

            if (ptr == IntPtr.Zero)
            {
                throw new CannotInterpretException(
                    String.Format("cannot map IntPtr.Zero"));
            }

            IntPtr typePtr = CPyMarshal.ReadPtrField(ptr, typeof(PyTypeObject), "ob_type");
            this.AttemptToMap(typePtr);

            if (!this.actualisableTypes.ContainsKey(typePtr))
            {
                throw new CannotInterpretException(
                    String.Format("cannot map object at {0} with type at {1}", ptr.ToString("x"), typePtr.ToString("x")));
            }
            this.actualisableTypes[typePtr](ptr);
        }

        
        public object 
        Retrieve(IntPtr ptr)
        {
            this.AttemptToMap(ptr);
            if (ptr == this._Py_NoneStruct)
            {
                return null;
            }

            if (this.incompleteObjects.ContainsKey(ptr))
            {
                switch (this.incompleteObjects[ptr])
                {
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
                        throw new Exception(String.Format("{0} pointed to unknown UDM", ptr.ToString("x")));
                }
            }
            return this.map.GetObj(ptr);
        }

        public int 
        RefCount(IntPtr ptr)
        {
            this.AttemptToMap(ptr);
            if (this.HasPtr(ptr))
            {
                if (this.map.HasPtr(ptr))
                {
                    this.map.UpdateStrength(ptr);
                }
                return CPyMarshal.ReadIntField(ptr, typeof(PyObject), "ob_refcnt");
            }
            else
            {
                throw new KeyNotFoundException(String.Format(
                    "RefCount: missing key in pointer map: {0}", ptr.ToString("x")));
            }
        }
        
        public void 
        IncRef(IntPtr ptr)
        {
            this.AttemptToMap(ptr);
            if (this.HasPtr(ptr))
            {
                int count = CPyMarshal.ReadIntField(ptr, typeof(PyObject), "ob_refcnt");
                CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", count + 1);
                if (this.map.HasPtr(ptr))
                {
                    this.map.UpdateStrength(ptr);
                }
            }
            else
            {
                throw new KeyNotFoundException(String.Format(
                    "IncRef: missing key in pointer map: {0}", ptr.ToString("x")));
            }
        }
        
        public void 
        DecRef(IntPtr ptr)
        {
            this.AttemptToMap(ptr);
            if (this.HasPtr(ptr))
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
                        throw new CannotInterpretException(String.Format(
                            "Cannot destroy object at {0} with type at {1}: no dealloc function", ptr.ToString("x"), typePtr.ToString("x")));
                    }
                    throw new CannotInterpretException(String.Format(
                        "Cannot destroy object at {0}: null type", ptr.ToString("x")));
                }
                else
                {
                    CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", count - 1);
                    if (this.map.HasPtr(ptr))
                    {
                        this.map.UpdateStrength(ptr);
                    }
                }
            }
            else
            {
                throw new KeyNotFoundException(String.Format(
                    "DecRef: missing key in pointer map: {0}", ptr.ToString("x")));
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
        CheckBridgePtrs()
        {
            this.map.CheckBridgePtrs();
        }

        public void Unmap(IntPtr ptr)
        {
            // TODO: very badly tested (things break fast if this isn't here, but...)
            if (this.map.HasPtr(ptr))
            {
                this.map.Release(ptr);
            }
            if (this.incompleteObjects.ContainsKey(ptr))
            {
                this.incompleteObjects.Remove(ptr);
            }
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
        
        
        public override IntPtr 
        GetAddress(string name)
        {
            IntPtr result = base.GetAddress(name);
            if (result != IntPtr.Zero)
            {
                return result;
            }

            switch (name)
            {
                case "PyBaseObject_Dealloc":
                    this.dgtMap[name] = new CPython_destructor_Delegate(this.PyBaseObject_Dealloc);
                    break;
                case "PyBaseObject_Init":
                    this.dgtMap[name] = new CPython_initproc_Delegate(this.PyBaseObject_Init);
                    break;
                case "PyCObject_Dealloc":
                    this.dgtMap[name] = new CPython_destructor_Delegate(this.PyCObject_Dealloc);
                    break;
                case "PyFile_Dealloc":
                    this.dgtMap[name] = new CPython_destructor_Delegate(this.PyFile_Dealloc);
                    break;
                case "PyFloat_New":
                    this.dgtMap[name] = new CPythonVarargsKwargsFunction_Delegate(this.PyFloat_New);
                    break;
                case "PyInt_New":
                    this.dgtMap[name] = new CPythonVarargsKwargsFunction_Delegate(this.PyInt_New);
                    break;
                case "PyList_Dealloc":
                    this.dgtMap[name] = new CPython_destructor_Delegate(this.PyList_Dealloc);
                    break;
                case "PySlice_Dealloc":
                    this.dgtMap[name] = new CPython_destructor_Delegate(this.PySlice_Dealloc);
                    break;
                case "PyTuple_Dealloc":
                    this.dgtMap[name] = new CPython_destructor_Delegate(this.PyTuple_Dealloc);
                    break;
                case "PyString_Str":
                    this.dgtMap[name] = new CPythonSelfFunction_Delegate(this.PyString_Str);
                    break;
                case "PyString_Concat_Core":
                    this.dgtMap[name] = new CPython_binaryfunc_Delegate(this.PyString_Concat_Core);
                    break;
                default:
                    this.unknownNames.Add(name);
                    return IntPtr.Zero;
            }
            return Marshal.GetFunctionPointerForDelegate(this.dgtMap[name]);
        }
        
        public override void
        Fill__Py_NoneStruct(IntPtr address)
        {
            PyObject none = new PyObject();
            none.ob_refcnt = 1;
            none.ob_type = this.PyNone_Type;
            Marshal.StructureToPtr(none, address, false);
            // no need to Associate: None/null is special-cased
        }

        public override void
        Fill__Py_ZeroStruct(IntPtr address)
        {
            PyIntObject False = new PyIntObject();
            False.ob_refcnt = 1;
            False.ob_type = this.PyBool_Type;
            False.ob_ival = 0;
            Marshal.StructureToPtr(False, address, false);
            this.map.Associate(address, false);
        }

        public override void
        Fill__Py_TrueStruct(IntPtr address)
        {
            PyIntObject True = new PyIntObject();
            True.ob_refcnt = 1;
            True.ob_type = this.PyBool_Type;
            True.ob_ival = 1;
            Marshal.StructureToPtr(True, address, false);
            this.map.Associate(address, true);
        }

        public override void
        Fill__Py_EllipsisObject(IntPtr address)
        {
            PyObject ellipsis = new PyObject();
            ellipsis.ob_refcnt = 1;
            ellipsis.ob_type = this.PyEllipsis_Type;
            Marshal.StructureToPtr(ellipsis, address, false);
            this.map.Associate(address, Builtin.Ellipsis);
        }

        public override void
        Fill__Py_NotImplementedStruct(IntPtr address)
        {
            PyObject notimpl = new PyObject();
            notimpl.ob_refcnt = 1;
            notimpl.ob_type = this.PyNotImplemented_Type;
            Marshal.StructureToPtr(notimpl, address, false);
            this.map.Associate(address, PythonOps.NotImplemented);
        }
        
        public override void
        Fill_Py_OptimizeFlag(IntPtr address)
        {
            CPyMarshal.WriteInt(address, 2);
        }
        
    }

}
