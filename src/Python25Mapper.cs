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
        public IntPtr 
        Allocate(int bytes)
        {
            return Marshal.AllocHGlobal(bytes);
        }
        public void 
        Free(IntPtr address)
        {
            Marshal.FreeHGlobal(address);
        }
    }

    public class Python25Mapper : PythonMapper
    {
        private PythonEngine engine;
        private Dictionary<IntPtr, object> ptrmap;
        private List<IntPtr> tempptrs;
        private IAllocator allocator;
        
        public Python25Mapper(PythonEngine eng): this(eng, new HGlobalAllocator())
        {            
        }
        
        public Python25Mapper(PythonEngine eng, IAllocator alloc)
        {
            this.engine = eng;
            this.allocator = alloc;
            this.ptrmap = new Dictionary<IntPtr, object>();
            this.tempptrs = new List<IntPtr>();
        }
        
        public IntPtr 
        Store(object obj)
        {
            IntPtr ptr = this.allocator.Allocate(Marshal.SizeOf(typeof(IntPtr)));
            CPyMarshal.WriteInt(ptr, 1);
            this.ptrmap[ptr] = obj;
            return ptr;
        }
        
        public object 
        Retrieve(IntPtr ptr)
        {
            return this.ptrmap[ptr];
        }
        
        public int 
        RefCount(IntPtr ptr)
        {
            if (this.ptrmap.ContainsKey(ptr))
            {
                return CPyMarshal.ReadInt(ptr);
            }
            else
            {
                throw new KeyNotFoundException("Missing key in pointer map");
            }
        }
        
        public void 
        IncRef(IntPtr ptr)
        {
            if (this.ptrmap.ContainsKey(ptr))
            {
                int count = CPyMarshal.ReadInt(ptr);
                CPyMarshal.WriteInt(ptr, count + 1);
            }
            else
            {
                throw new KeyNotFoundException("Missing key in pointer map");
            }
        }
        
        public void 
        DecRef(IntPtr ptr)
        {
            if (this.ptrmap.ContainsKey(ptr))
            {
                int count = CPyMarshal.ReadInt(ptr);
                if (count == 1)
                {
                    this.Delete(ptr);
                }
                else
                {
                    CPyMarshal.WriteInt(ptr, count - 1);
                }
            }
            else
            {
                throw new KeyNotFoundException("Missing key in pointer map");
            }
        }
        
        public void 
        Delete(IntPtr ptr)
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

        public void RememberTempPtr(IntPtr ptr)
        {
            this.tempptrs.Add(ptr);
        }

        public void FreeTempPtrs()
        {
            foreach (IntPtr ptr in this.tempptrs)
            {
                this.allocator.Free(ptr);
            }
            this.tempptrs.Clear();
        }
        
        public override IntPtr 
        Py_InitModule4(string name, IntPtr methods, string doc, IntPtr self, int apiver)
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
            moduleCode.Append("  _jumpy_mapper.FreeTempPtrs()\n");
            moduleCode.Append("  _jumpy_mapper.DecRef(argPtr)\n");
            
            moduleCode.Append("def _jumpy_dispatch_kwargs(name, args, kwargs):\n");
            moduleCode.Append("  argPtr = _jumpy_mapper.Store(args)\n");
            moduleCode.Append("  kwargPtr = _jumpy_mapper.Store(kwargs)\n");
            moduleCode.Append("  _jumpy_dispatch_table[name](IntPtr.Zero, argPtr, kwargPtr)\n");
            moduleCode.Append("  _jumpy_mapper.FreeTempPtrs()\n");
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


        protected virtual Dictionary<int, object> 
        GetArgValues(IntPtr args, IntPtr kwargs, IntPtr kwlist)
        {
            Tuple actualArgs = (Tuple)this.Retrieve(args);
            Dict actualKwargs = (Dict)this.Retrieve(kwargs);

            Dictionary<int, object> result = new Dictionary<int, object>();
            for (int i = 0; i < actualArgs.GetLength(); i++)
            {
                result[i] = actualArgs[i];
            }
            
            int intPtrSize = Marshal.SizeOf(typeof(IntPtr));
            int index = 0;
            IntPtr currentKw = kwlist;
            while (Marshal.ReadIntPtr(currentKw) != IntPtr.Zero)
            {
                IntPtr addressToRead = CPyMarshal.ReadPtr(currentKw);
                string thisKey = Marshal.PtrToStringAnsi(addressToRead);
                if (actualKwargs.ContainsKey(thisKey))
                {
                    result[index] = actualKwargs[thisKey];
                }
                currentKw = (IntPtr)(currentKw.ToInt32() + intPtrSize);
                index++;
            }
        
            return result;
        }

        protected virtual Dictionary<int, ArgWriter> 
        GetArgWriters(string format)
        {
            Dictionary<int, ArgWriter> result = new Dictionary<int, ArgWriter>();
            string trimmedFormat = format;
            int argIndex = 0;
            int nextStartPointer = 0;
            while (trimmedFormat.Length > 0 && !trimmedFormat.StartsWith(":"))
            {
                if (trimmedFormat.StartsWith("|"))
                {
                    trimmedFormat = trimmedFormat.Substring(1);
                    continue;
                }
                
                if (trimmedFormat.StartsWith("i"))
                {
                    trimmedFormat = trimmedFormat.Substring(1);
                    result[argIndex] = new IntArgWriter(nextStartPointer);
                }
                else if (trimmedFormat.StartsWith("s#"))
                {
                    trimmedFormat = trimmedFormat.Substring(2);
                    result[argIndex] = new SizedStringArgWriter(nextStartPointer, this);
                }
                else
                {
                    throw new NotImplementedException(String.Format(
                        "Unrecognised characters in format string, starting at: {0}", 
                        trimmedFormat));
                }
                nextStartPointer = result[argIndex].NextWriterStartIndex;
                argIndex++;
            }
            return result;
        }


        protected virtual void 
        SetArgValues(Dictionary<int, object> argsToWrite, 
                     Dictionary<int, ArgWriter> argWriters, 
                     IntPtr outPtr)
        {
            foreach (KeyValuePair<int,object> p in argsToWrite)
            {
                argWriters[p.Key].Write(outPtr, p.Value);
            }
        }


        public override int 
        PyArg_ParseTupleAndKeywords(IntPtr args, 
                                    IntPtr kwargs, 
                                    string format, 
                                    IntPtr kwlist, 
                                    IntPtr outPtr)
        {
            Dictionary<int, object> argsToWrite = this.GetArgValues(args, kwargs, kwlist);
            Dictionary<int, ArgWriter> argWriters = this.GetArgWriters(format);
            this.SetArgValues(argsToWrite, argWriters, outPtr);
            return 1;
        }
    }

}
