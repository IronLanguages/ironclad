using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

using IronPython.Hosting;
using IronPython.Runtime;

namespace JumPy
{
    public interface IAllocator
    {
        IntPtr Allocate(int bytes);
        void Free(IntPtr address);
    }
    
    public class HGlobalAllocator : IAllocator
    {
        public IntPtr Allocate(int bytes)
        {
            return Marshal.AllocHGlobal(bytes);
        }
        public void Free(IntPtr address)
        {
            Marshal.FreeHGlobal(address);
        }
    }

    public class Python25Mapper : PythonMapper
    {
        private PythonEngine engine;
        private Dictionary<IntPtr, object> ptrmap;
        private IAllocator allocator;
        
        public Python25Mapper(PythonEngine eng): this(eng, new HGlobalAllocator())
        {            
        }
        
        public Python25Mapper(PythonEngine eng, IAllocator alloc)
        {
            this.engine = eng;
            this.allocator = alloc;
            this.ptrmap = new Dictionary<IntPtr, object>();
        }
        
        public IntPtr Store(object obj)
        {
            IntPtr ptr = this.allocator.Allocate(4);
            Marshal.WriteInt32(ptr, 1);
            this.ptrmap[ptr] = obj;
            return ptr;
        }
        
        public object Retrieve(IntPtr ptr)
        {
            return this.ptrmap[ptr];
        }
        
        public int RefCount(IntPtr ptr)
        {
            if (this.ptrmap.ContainsKey(ptr))
            {
                return Marshal.ReadInt32(ptr);
            }
            else
            {
                throw new KeyNotFoundException("Missing key in pointer map");
            }
        }
        
        public void IncRef(IntPtr ptr)
        {
            if (this.ptrmap.ContainsKey(ptr))
            {
                int count = Marshal.ReadInt32(ptr);
                Marshal.WriteInt32(ptr, count + 1);
            }
            else
            {
                throw new KeyNotFoundException("Missing key in pointer map");
            }
        }
        
        public void DecRef(IntPtr ptr)
        {
            if (this.ptrmap.ContainsKey(ptr))
            {
                int count = Marshal.ReadInt32(ptr);
                if (count == 1)
                {
                    this.Delete(ptr);
                }
                else
                {
                    Marshal.WriteInt32(ptr, count - 1);
                }
            }
            else
            {
                throw new KeyNotFoundException("Missing key in pointer map");
            }
        }
        
        public void Delete(IntPtr ptr)
        {
            if (this.ptrmap.ContainsKey(ptr))
            {
                this.ptrmap.Remove(ptr);
                this.allocator.Free(ptr);
            }
            else
            {
                throw new KeyNotFoundException("Missing key in pointer map");
            }
        }
        
        public override IntPtr Py_InitModule4(string name, IntPtr methods, string doc, IntPtr self, int apiver)
        {
            Dictionary<string, object> globals = new Dictionary<string, object>();
            globals["_jumpy_mapper"] = this;
            globals["__doc__"] = doc;
            
            Dictionary<string, Delegate> methodTable = new Dictionary<string, Delegate>();
            globals["_jumpy_dispatch_table"] = methodTable;
            
            StringBuilder moduleCode = new StringBuilder();
            moduleCode.Append("from System import IntPtr\n");
            
            moduleCode.Append("def _jumpy_dispatch(name, args):\n");
            moduleCode.Append("  argPtr = _jumpy_mapper.Store(args)\n");
            moduleCode.Append("  _jumpy_dispatch_table[name](IntPtr.Zero, argPtr)\n");
            moduleCode.Append("  _jumpy_mapper.DecRef(argPtr)\n");
            
            moduleCode.Append("def _jumpy_dispatch_kwargs(name, args, kwargs):\n");
            moduleCode.Append("  argPtr = _jumpy_mapper.Store(args)\n");
            moduleCode.Append("  kwargPtr = _jumpy_mapper.Store(kwargs)\n");
            moduleCode.Append("  _jumpy_dispatch_table[name](IntPtr.Zero, argPtr, kwargPtr)\n");
            moduleCode.Append("  _jumpy_mapper.DecRef(argPtr)\n");
            moduleCode.Append("  _jumpy_mapper.DecRef(kwargPtr)\n");
            
            IntPtr methodPtr = methods;
            while (Marshal.ReadInt32(methodPtr) != 0)
            {
                PyMethodDef thisMethod = (PyMethodDef)Marshal.PtrToStructure(methodPtr, typeof(PyMethodDef));
                
                switch (thisMethod.ml_flags)
                {
                    case METH.VARARGS:
                        moduleCode.Append(String.Format(
                            "\ndef {0}(*args):\n  '''{1}'''\n  _jumpy_dispatch('{0}', args)\n",
                            thisMethod.ml_name, thisMethod.ml_doc));
                        methodTable[thisMethod.ml_name] = 
                            (CPythonVarargsFunction_Delegate)
                            Marshal.GetDelegateForFunctionPointer(
                                thisMethod.ml_meth, 
                                typeof(CPythonVarargsFunction_Delegate));
                        break;
                
                    case METH.VARARGS | METH.KEYWORDS:
                        moduleCode.Append(String.Format(
                            "\ndef {0}(*args, **kwargs):\n  '''{1}'''\n  _jumpy_dispatch_kwargs('{0}', args, kwargs)\n",
                            thisMethod.ml_name, thisMethod.ml_doc));
                        methodTable[thisMethod.ml_name] = 
                            (CPythonVarargsKwargsFunction_Delegate)
                            Marshal.GetDelegateForFunctionPointer(
                                thisMethod.ml_meth, 
                                typeof(CPythonVarargsKwargsFunction_Delegate));
                        break;

                    default:
                        throw new Exception("unsupported method flags");
                }
                
                methodPtr = (IntPtr)(methodPtr.ToInt32() + Marshal.SizeOf(typeof(PyMethodDef)));
            }
            
            EngineModule module = this.engine.CreateModule(name, globals, true);
            this.engine.Execute(moduleCode.ToString(), module);
            return this.Store(module);
        }

        public override bool PyArg_ParseTupleAndKeywords(IntPtr args, IntPtr kwargs, string format, IntPtr kwlist, IntPtr argPtr)
        {
            Tuple actualArgs = (Tuple)this.Retrieve(args);
            Dict actualKwargs = (Dict)this.Retrieve(kwargs);

            Dictionary<int, object> nondefaults = new Dictionary<int, object>();
            for (int i = 0; i < actualArgs.GetLength(); i++)
            {
                nondefaults[i] = actualArgs[i];
            }
            
            int intPtrSize = Marshal.SizeOf(typeof(IntPtr));
            int index = 0;
            IntPtr currentKw = kwlist;
            while (Marshal.ReadIntPtr(currentKw) != IntPtr.Zero)
            {
                IntPtr addressToRead = Marshal.ReadIntPtr(currentKw);
                string thisKey = Marshal.PtrToStringUni(addressToRead);
                if (actualKwargs.ContainsKey(thisKey))
                {
                    nondefaults[index] = actualKwargs[thisKey];
                }
                currentKw = (IntPtr)(currentKw.ToInt32() + intPtrSize);
                index++;
            }
            
            foreach (KeyValuePair<int,object> p in nondefaults)
            {
                int k = (int)p.Key;
                IntPtr addressToWrite = Marshal.ReadIntPtr((IntPtr)(argPtr.ToInt32() + (k * intPtrSize)));
                
                int v = (int)p.Value;
                Marshal.WriteInt32(addressToWrite, v);
            }

            return true;
        }
    }

}
