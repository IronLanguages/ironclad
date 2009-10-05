using System;
using System.IO;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Threading;

using IronPython.Hosting;
using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

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

        private PythonModule scratchModule;
        private CodeContext scratchContext;

        private object removeSysHacks;
        private object kindaDictProxy;
        private object kindaSeqIter;
        private object cFileClass;
        private Lock GIL;

        private bool alive = false;
        private bool logErrors = false;
        private bool appliedNumpyHack = false;
        private bool appliedScipyHack = false;
        
        private InterestingPtrMap map = new InterestingPtrMap();
        private Dictionary<IntPtr, ActualiseDelegate> actualisableTypes = new Dictionary<IntPtr, ActualiseDelegate>();
        private Dictionary<IntPtr, object> classStubs = new Dictionary<IntPtr, object>();
        private Dictionary<IntPtr, UnmanagedDataMarker> incompleteObjects = new Dictionary<IntPtr, UnmanagedDataMarker>();
        private Dictionary<IntPtr, List> listsBeingActualised = new Dictionary<IntPtr, List>();
        private Dictionary<string, IntPtr> internedStrings = new Dictionary<string, IntPtr>();
        private Dictionary<IntPtr, IntPtr> FILEs = new Dictionary<IntPtr, IntPtr>();
        private List<IntPtr> tempObjects = new List<IntPtr>();
        private Stack<dgt_void_void> exitfuncs = new Stack<dgt_void_void>();

        private LocalDataStoreSlot threadLockStore = Thread.AllocateDataSlot();
        private LocalDataStoreSlot threadStateStore = Thread.AllocateDataSlot();

        // TODO: must be a better way to handle imports...
        // public to allow manipulation from test code
        public Stack<string> importNames = new Stack<string>();
        public Stack<string> importFiles = new Stack<string>();
        
        
        public Python25Mapper(CodeContext context): 
          this(context, null, new HGlobalAllocator())
        {
        }
        
        public Python25Mapper(CodeContext context, string stubPath): 
          this(context, stubPath, new HGlobalAllocator())
        {
        }
        
        public Python25Mapper(CodeContext context, IAllocator allocator):
          this(context, null, allocator)
        {
        }

        public Python25Mapper(CodeContext context, string stubPath, IAllocator allocator):
          this(context.LanguageContext, stubPath, allocator)
        {
        }

        public Python25Mapper(PythonContext python, string stubPath, IAllocator allocator)
        {
            this.Init(python, stubPath, allocator);
        }
        
        ~Python25Mapper()
        {
            // alive check is here so that we don't crash hard on failed construct
            if (this.alive)
            {
                throw new Exception("Python25Mappers need to be Disposed manually. Please don't just leave them lying around.");
            }
        }

        private void Init(PythonContext inPython, string stubPath, IAllocator inAllocator)
        {
            this.GIL = new Lock();
            this.python = inPython;
            this.allocator = inAllocator;
            
            this.importNames.Push("");
            this.importFiles.Push(null);
            
            this.CreateScratchModule();
            this.kindaDictProxy = this.CreateFromSnippet(CodeSnippets.KINDA_DICT_PROXY_CODE, "KindaDictProxy");
            this.kindaSeqIter = this.CreateFromSnippet(CodeSnippets.KINDA_SEQ_ITER_CODE, "KindaSeqIter");
            
            if (stubPath != null)
            {
                // this appears to be necessary if you want to run functionalitytest.py on its own
                Unmanaged.LoadLibrary("msvcr90.dll");
                
                this.stub = new StubReference(stubPath);
                this.stub.Init(new AddressGetterDelegate(this.GetAddress), new DataSetterDelegate(this.SetData));

                string path = Environment.GetEnvironmentVariable("PATH");
                string newpath = path + ";" + Path.Combine(Path.GetDirectoryName(stubPath), "support");
                Environment.SetEnvironmentVariable("PATH", newpath);

                this.ReadyBuiltinTypes();
                this.importer = new PydImporter();
                this.removeSysHacks = this.CreateFromSnippet(CodeSnippets.INSTALL_IMPORT_HOOK_CODE, "remove_sys_hacks");
                
                // TODO: load builtin modules only on demand?
                this.stub.LoadBuiltinModule("posix");
                this.stub.LoadBuiltinModule("mmap");
                this.stub.LoadBuiltinModule("_csv");
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
                IntPtr typePtr = CPyMarshal.ReadPtrField(ptr, typeof(PyObject), "ob_type");
                if (typePtr == IntPtr.Zero)
                {
                    // no type
                    return;
                }
                
                if (CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_dealloc") == IntPtr.Zero)
                {
                    // no dealloc function
                    return;
                }
                
                dgt_void_ptr dealloc = (dgt_void_ptr)
                    CPyMarshal.ReadFunctionPtrField(
                        typePtr, typeof(PyTypeObject), "tp_dealloc", typeof(dgt_void_ptr));
                dealloc(ptr);
            }
            
            // not really surprised to see these errors...
            catch (BadMappingException) {}
            catch (AccessViolationException) {}
            catch (NullReferenceException) {}
            
            // may be worth mentioning other errors though
            catch (Exception e)
            {
                if (this.logErrors)
                {
                    Console.WriteLine("unexpected error during DumpPtr:\n{0}", e);
                }
            }
        }
        
        protected virtual void 
        Dispose(bool disposing)
        {
            if (!this.alive)
            {
                return;
            }

            this.alive = false;
            while (this.exitfuncs.Count > 0)
            {
                this.exitfuncs.Pop()();
            }

            if (!this.appliedNumpyHack)
            {
                // TODO: FIXME?
                // I don't know what it is about numpy, but using it heavily
                // makes this step extremely flaky: that's, like, BSOD flaky.
                // OTOH, even attempting this operation is very optimistic
                // indeed, and it's only really here so that I can repeatedly
                // construct/destroy mappers -- without leaking *too* much --
                // during test runs. In the wild, all this will be reclaimed
                // by the operating system at process shutdown time anyway.
                this.map.MapOverBridgePtrs(new PtrFunc(this.DumpPtr));
            }
            
            this.allocator.FreeAll();
            foreach (IntPtr FILE in this.FILEs.Values)
            {
                Unmanaged.fclose(FILE);
            }
            
            if (this.stub != null)
            {
                PythonCalls.Call(this.removeSysHacks);
                
                PythonDictionary modules = (PythonDictionary)this.python.SystemState.__dict__["modules"];
                modules.Remove("mmap");
                modules.Remove("posix");
                modules.Remove("_csv");
                if (modules.Contains("csv"))
                {
                    modules.Remove("csv");
                }
                
                this.importer.Dispose();
                this.stub.Dispose();
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
                this.GIL.Dispose();
            }
        }

        public bool
        Alive
        {
            get { return this.alive; }
        }
        
        public int
        GCThreshold
        {
            get { return this.map.GCThreshold; }
            set { this.map.GCThreshold = value; }
        }
        
        public bool
        LogErrors
        {
            get { return this.logErrors; }
            set { this.logErrors = value; }
        }

        public object
        CPyFileClass
        {
            get { return this.cFileClass; }
        }
        
        public void
        LogMappingInfo(object id)
        {
            this.GIL.Acquire();
            try
            {
                this.map.LogMappingInfo(id);
            }
            finally
            {
                this.GIL.Release();
            }
        }
        
        public void
        LogRefs()
        {
            this.GIL.Acquire();
            try
            {
                this.map.LogRefs();
            }
            finally
            {
                this.GIL.Release();
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
            IntPtr ptr = this.allocator.Alloc((uint)Marshal.SizeOf(typeof(PyObject)));
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
                throw new CannotInterpretException("cannot map IntPtr.Zero");
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
                        this.ActualiseList(ptr);
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
            
            if (!this.HasPtr(ptr))
            {
                throw new KeyNotFoundException(String.Format(
                    "RefCount: missing key in pointer map: {0}", ptr.ToString("x")));
            }
            
            if (this.map.HasPtr(ptr))
            {
                this.map.UpdateStrength(ptr);
            }
            
            return CPyMarshal.ReadIntField(ptr, typeof(PyObject), "ob_refcnt");
        }
        
        public void 
        IncRef(IntPtr ptr)
        {
            this.AttemptToMap(ptr);
            
            if (!this.HasPtr(ptr))
            {
                throw new KeyNotFoundException(String.Format(
                    "IncRef: missing key in pointer map: {0}", ptr.ToString("x")));
            }
            
            int count = CPyMarshal.ReadIntField(ptr, typeof(PyObject), "ob_refcnt");
            CPyMarshal.WriteIntField(ptr, typeof(PyObject), "ob_refcnt", count + 1);
            
            if (this.map.HasPtr(ptr))
            {
                this.map.UpdateStrength(ptr);
            }
        }
        
        public void 
        DecRef(IntPtr ptr)
        {
            this.AttemptToMap(ptr);
            
            if (!this.HasPtr(ptr))
            {
                throw new KeyNotFoundException(String.Format(
                    "DecRef: missing key in pointer map: {0}", ptr.ToString("x")));
            }
            
            int count = CPyMarshal.ReadIntField(ptr, typeof(PyObject), "ob_refcnt");
            if (count == 0)
            {
                throw new BadRefCountException("Trying to DecRef an object with ref count 0");
            }
            else if (count == 1)
            {
                IntPtr typePtr = CPyMarshal.ReadPtrField(ptr, typeof(PyObject), "ob_type");
                if (typePtr == IntPtr.Zero)
                {
                    throw new CannotInterpretException(String.Format(
                        "Cannot destroy object at {0}: null type", ptr.ToString("x")));
                }
                
                if (CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_dealloc") == IntPtr.Zero)
                {
                    throw new CannotInterpretException(String.Format(
                        "Cannot destroy object at {0} with type at {1}: no dealloc function", ptr.ToString("x"), typePtr.ToString("x")));
                }

                dgt_void_ptr deallocDgt = (dgt_void_ptr)CPyMarshal.ReadFunctionPtrField(
                    typePtr, typeof(PyTypeObject), "tp_dealloc", typeof(dgt_void_ptr));
                deallocDgt(ptr);
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
        
        public void 
        Strengthen(object obj)
        {
            this.GIL.Acquire();
            try
            {
                this.map.Strengthen(obj);
            }
            finally
            {
                this.GIL.Release();
            }
        }
        
        public void 
        Weaken(object obj)
        {
            this.GIL.Acquire();
            try
            {
                this.map.Weaken(obj);
            }
            finally
            {
                this.GIL.Release();
            }
        }
        
        public void
        ForceCleanup()
        {
            if (!this.alive)
            {
                return;
            }
            
            this.GIL.Acquire();
            try
            {
                this.map.CheckBridgePtrs(true);
            }
            finally
            {
                this.GIL.Release();
            }
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

        public void
        DecRefLater(IntPtr ptr)
        {
            this.tempObjects.Add(ptr);
        }

        public override int
        Py_AtExit(IntPtr exitfuncPtr)
        {
            dgt_void_void exitfunc = (dgt_void_void)Marshal.GetDelegateForFunctionPointer(
                exitfuncPtr, typeof(dgt_void_void));
            this.exitfuncs.Push(exitfunc);
            return 0;
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
            this.map.Associate(address, Builtin.False);
        }

        public override void
        Fill__Py_TrueStruct(IntPtr address)
        {
            PyIntObject True = new PyIntObject();
            True.ob_refcnt = 1;
            True.ob_type = this.PyBool_Type;
            True.ob_ival = 1;
            Marshal.StructureToPtr(True, address, false);
            this.map.Associate(address, Builtin.True);
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
        
        public override void
        Fill__PyThreadState_Current(IntPtr address)
        {
            CPyMarshal.WritePtr(address, IntPtr.Zero);
        }

        private object CreateFromSnippet(string code, string key)
        {
            this.ExecInModule(code, this.scratchModule);
            return this.scratchModule.__dict__[key];
        }
    }

}
