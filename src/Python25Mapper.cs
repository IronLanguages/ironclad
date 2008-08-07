using System;
using System.IO;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Threading;

using IronPython.Runtime;
using IronPython.Runtime.Calls;
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

    public class CannotInterpretException : Exception
    {
        public CannotInterpretException(string message): base(message)
        {
        }
    }


    public partial class Python25Mapper : Python25Api
    {
        private bool alive = false;
        private ScriptEngine engine;
        private StubReference stub;
        private PydImporter importer;
        private IAllocator allocator;
        private InterestingPtrMap map = new InterestingPtrMap();

        private PythonModule scratchModule;
        private PythonModule dispatcherModule;
        private object dispatcherClass;
        private object trivialObjectSubclass;

        private StupidSet bridgePtrs = new StupidSet();
        private List<IntPtr> tempObjects = new List<IntPtr>();
        private Dictionary<IntPtr, IntPtr> FILEs = new Dictionary<IntPtr, IntPtr>();
        private Dictionary<IntPtr, List> listsBeingActualised = new Dictionary<IntPtr, List>();
        private Dictionary<string, IntPtr> internedStrings = new Dictionary<string, IntPtr>();
        private LocalDataStoreSlot threadDictStore = Thread.AllocateDataSlot();
        private StupidSet notInterpretableTypes = new StupidSet();

        // TODO: this should probably be thread-local too
        private object _lastException = null;

        // one day, perhaps, this 'set' will be empty
        private StupidSet unknownNames = new StupidSet();

        // TODO must be a better way to handle imports...
        private string importName = "";
        private string importPath = null;
        
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
                this.ReadyBuiltinTypes();
                this.importer = new PydImporter();
                
                string path = Environment.GetEnvironmentVariable("IRONPYTHONPATH");
                if (path != null && path.Length > 0)
                {
                    string[] paths = path.Split(Path.PathSeparator);
                    foreach (string p in paths) 
                    {
                        this.AddToPath(p);
                    }
                }
                // TODO: work out why this line causes leakage
                this.ExecInModule(CodeSnippets.INSTALL_IMPORT_HOOK_CODE, this.scratchModule);
            }
            this.alive = true;
        }

        ~Python25Mapper()
        {
            if (this.alive)
            {
                Console.WriteLine("Python25Mapper finalized without being Disposed: I'm not even going to try to handle this.");
            }
        }
        
        public void Dispose()
        {
            /* You must call Dispose(); really, you must call Dispose(). Shutdown seems to be reliably clean if you
             * Dispose() *after* delling all ipy references to bridge objects, and *before* deallocing any memory the 
             * mapper might have an interest in (specifically, anything you didn't allocate with the same allocator
             * that the mapper uses -- for example, the Py*_Type pointers).
             */
 
            this.CheckBridgePtrs();
            GC.Collect();
            GC.WaitForPendingFinalizers();
            GC.Collect();
            GC.WaitForPendingFinalizers();
            /* The preceding dance is intended to ensure that no bridge objects are
             * sitting around in the freachable queue waiting to be double-freed 
             * (AFAICT, SuppressFinalize does not affect objects already on the 
             * freachable queue; hence, for such objects, the dealloc function would 
             * be called once in the following loop and once at some point in the 
             * future.)
             * 
             * If the above is nonsense, please complain :).
             */

            foreach (object ptr in this.bridgePtrs.ElementsArray)
            {
                GC.SuppressFinalize(this.Retrieve((IntPtr)ptr));
                IntPtr typePtr = CPyMarshal.ReadPtrField((IntPtr)ptr, typeof(PyObject), "ob_type");
                CPython_destructor_Delegate dgt = (CPython_destructor_Delegate)
                    CPyMarshal.ReadFunctionPtrField(
                        typePtr, typeof(PyTypeObject), "tp_dealloc", typeof(CPython_destructor_Delegate));
                dgt((IntPtr)ptr);
            }
            this.alive = false;
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

        public bool
        Alive
        {
            get { return this.alive; }
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
        StoreBridge(IntPtr ptr, object obj)
        {
            this.map.WeakAssociate(ptr, obj);
            this.bridgePtrs.Add(ptr);
            this.Strengthen(obj);
        }
        
        
        public bool
        HasPtr(IntPtr ptr)
        {
            return this.map.HasPtr(ptr);
        }
        

        private void
        AttemptToMap(IntPtr ptr)
        {
            if (this.map.HasPtr(ptr) || ptr == IntPtr.Zero)
            {
                return;
            }

            IntPtr typePtr = CPyMarshal.ReadPtrField(ptr, typeof(PyTypeObject), "ob_type");
            this.AttemptToMap(typePtr);

            if (typePtr == IntPtr.Zero || this.notInterpretableTypes.Contains(typePtr))
            {
                throw new CannotInterpretException(String.Format("cannot translate object at {0} with type at {1}", ptr, typePtr));
            }

            if (typePtr == this.PyType_Type)
            {
                this.ActualiseType(ptr);
                return;
            }
            
            if (typePtr == this.PyList_Type ||
                typePtr == this.PyString_Type ||
                typePtr == this.PyTuple_Type)
            {
                throw new NotImplementedException("trying to interpret a string, list, or tuple from unmapped unmanaged memory");
            }

            object managedInstance = PythonCalls.Call(this.trivialObjectSubclass);
            Builtin.setattr(DefaultContext.Default, managedInstance, "_instancePtr", ptr);
            Builtin.setattr(DefaultContext.Default, managedInstance, "__class__", this.Retrieve(typePtr));
            this.StoreBridge(ptr, managedInstance);
            this.IncRef(ptr);
        }

        
        public object 
        Retrieve(IntPtr ptr)
        {
            this.AttemptToMap(ptr);
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
            return this.map.GetObj(ptr);
        }

        public int 
        RefCount(IntPtr ptr)
        {
            this.AttemptToMap(ptr);
            if (this.map.HasPtr(ptr))
            {
                int count = CPyMarshal.ReadIntField(ptr, typeof(PyObject), "ob_refcnt");
                if (this.bridgePtrs.Contains(ptr))
                {
                    object obj = this.Retrieve(ptr);
                    if (count > 1)
                    {
                        this.Strengthen(obj);
                    }
                    else
                    {
                        this.Weaken(obj);
                    }
                }
                return count;
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
            this.AttemptToMap(ptr);
            if (this.map.HasPtr(ptr))
            {
                int count = CPyMarshal.ReadIntField(ptr, typeof(PyObject), "ob_refcnt");
                if (count == 1 && this.bridgePtrs.Contains(ptr))
                {
                    this.Strengthen(this.Retrieve(ptr));
                }
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
            this.AttemptToMap(ptr);
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
                    if (count == 2 && this.bridgePtrs.Contains(ptr))
                    {
                        this.Weaken(this.Retrieve(ptr));
                    }
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
        CheckBridgePtrs()
        {
            foreach (object ptro in this.bridgePtrs.ElementsArray)
            {
                IntPtr ptr = (IntPtr)ptro;
                int count = CPyMarshal.ReadIntField(ptr, typeof(PyObject), "ob_refcnt");
                if (count == 1)
                {
                    this.Weaken(this.Retrieve(ptr));
                }
                if (count == 2)
                {
                    this.Strengthen(this.Retrieve(ptr));
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
            this.Unmap(ptr);
            this.allocator.Free(ptr);
        }

        public void Unmap(IntPtr ptr)
        {
            // TODO: very badly tested (nothing works if this isn't here, but...)
            this.bridgePtrs.RemoveIfPresent(ptr);
            if (this.map.HasPtr(ptr))
            {
                this.map.Release(ptr);
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
                case "PyTuple_Dealloc":
                    this.dgtMap[name] = new CPython_destructor_Delegate(this.PyTuple_Dealloc);
                    break;
                case "PyList_Dealloc":
                    this.dgtMap[name] = new CPython_destructor_Delegate(this.PyList_Dealloc);
                    break;
                case "PyCObject_Dealloc":
                    this.dgtMap[name] = new CPython_destructor_Delegate(this.PyCObject_Dealloc);
                    break;
                
                default:
                    this.unknownNames.Add(name);
                    return IntPtr.Zero;
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
        
        
        public override void
        Fill_Py_OptimizeFlag(IntPtr address)
        {
            CPyMarshal.WriteInt(address, 2);
        }
        
    }

}
