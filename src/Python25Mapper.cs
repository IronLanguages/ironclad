using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

using IronPython.Hosting;
using IronPython.Runtime;

using JumPy.Structs;

namespace JumPy
{
    public interface IAllocator
    {
        IntPtr Alloc(int bytes);
        IntPtr Realloc(IntPtr old, int bytes);
        void Free(IntPtr address);
    }
    
    public class HGlobalAllocator : IAllocator
    {
        public IntPtr 
        Alloc(int bytes)
        {
            return Marshal.AllocHGlobal(bytes);
        }
        public IntPtr
        Realloc(IntPtr old, int bytes)
        {
        	return Marshal.ReAllocHGlobal(old, (IntPtr)bytes);
        }
        public void 
        Free(IntPtr address)
        {
            Marshal.FreeHGlobal(address);
        }
    }

	public enum UnmanagedDataMarker
	{
		PyStringObject,
	}


    public class Python25Mapper : PythonMapper
    {
    	private const string MODULE_CODE = @"
from System import IntPtr

def _cleanup(*args):
  _jumpy_mapper.FreeTempPtrs()
  for arg in args:
  	if arg != IntPtr.Zero:
  	  _jumpy_mapper.DecRef(arg)

def _raiseExceptionIfRequired():
  error = _jumpy_mapper.LastException
  if error:
    _jumpy_mapper.LastException = None
    raise error
  
def _jumpy_dispatch(name, args):
  argPtr = _jumpy_mapper.Store(args)
  resultPtr = _jumpy_dispatch_table[name](IntPtr.Zero, argPtr)
  try:
    _raiseExceptionIfRequired()
    return _jumpy_mapper.Retrieve(resultPtr)
  finally:
    _cleanup(argPtr, resultPtr)

def _jumpy_dispatch_kwargs(name, args, kwargs):
  argPtr = _jumpy_mapper.Store(args)
  kwargPtr = _jumpy_mapper.Store(kwargs)
  resultPtr = _jumpy_dispatch_table[name](IntPtr.Zero, argPtr, kwargPtr)
  try:
    _raiseExceptionIfRequired()
    return _jumpy_mapper.Retrieve(resultPtr)
  finally:
    _cleanup(argPtr, kwargPtr, resultPtr)
  
";
    
        private PythonEngine engine;
        private Dictionary<IntPtr, object> ptrmap;
        private List<IntPtr> tempptrs;
        private IAllocator allocator;
        private Exception _lastException;
        
        public Python25Mapper(PythonEngine eng): this(eng, new HGlobalAllocator())
        {            
        }
        
        public Python25Mapper(PythonEngine eng, IAllocator alloc)
        {
            this.engine = eng;
            this.allocator = alloc;
            this.ptrmap = new Dictionary<IntPtr, object>();
            this.tempptrs = new List<IntPtr>();
            this._lastException = null;
        }
        
        public IntPtr 
        Store(object obj)
        {
            IntPtr ptr = this.allocator.Alloc(Marshal.SizeOf(typeof(IntPtr)));
            CPyMarshal.WriteInt(ptr, 1);
            this.ptrmap[ptr] = obj;
            return ptr;
        }
        
        private void
        StoreUnmanagedData(IntPtr ptr, UnmanagedDataMarker marker)
        {
        	this.ptrmap[ptr] = marker;
        }
        
        private static char
        CharFromByte(byte b)
        {
        	return (char)b;
        }
        
        public object 
        Retrieve(IntPtr ptr)
        {
        	object possibleMarker = this.ptrmap[ptr];
        	if (possibleMarker.GetType() == typeof(UnmanagedDataMarker))
        	{
        		UnmanagedDataMarker marker = (UnmanagedDataMarker)possibleMarker;
        		switch (marker)
        		{
        			case UnmanagedDataMarker.PyStringObject:
        				IntPtr buffer = CPyMarshal.Offset(ptr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
        				IntPtr lengthPtr = CPyMarshal.Offset(ptr, Marshal.OffsetOf(typeof(PyStringObject), "ob_size"));
        				int length = CPyMarshal.ReadInt(lengthPtr);
        				
        				byte[] bytes = new byte[length];
        				Marshal.Copy(buffer, bytes, 0, length);
        				char[] chars = Array.ConvertAll<byte, char>(
        					bytes, new Converter<byte, char>(CharFromByte));
        				this.ptrmap[ptr] = new string(chars);
        				break;
        			
        			default:
        				throw new Exception("Found impossible data in pointer map");
        		}
        	}
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
                return 0;
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
        
        public Exception LastException
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
        
        public override IntPtr 
        Py_InitModule4(string name, IntPtr methods, string doc, IntPtr self, int apiver)
        {
            Dictionary<string, object> globals = new Dictionary<string, object>();
            globals["_jumpy_mapper"] = this;
            globals["__doc__"] = doc;
            
            Dictionary<string, Delegate> methodTable = new Dictionary<string, Delegate>();
            globals["_jumpy_dispatch_table"] = methodTable;
            
            StringBuilder moduleCode = new StringBuilder();
            moduleCode.Append(MODULE_CODE);
            
            IntPtr methodPtr = methods;
            while (Marshal.ReadInt32(methodPtr) != 0)
            {
                PyMethodDef thisMethod = (PyMethodDef)Marshal.PtrToStructure(methodPtr, typeof(PyMethodDef));
                
                switch (thisMethod.ml_flags)
                {
                    case METH.VARARGS:
                        moduleCode.Append(String.Format(
                            "\ndef {0}(*args):\n  '''{1}'''\n  return _jumpy_dispatch('{0}', args)\n",
                            thisMethod.ml_name, thisMethod.ml_doc));
                        methodTable[thisMethod.ml_name] = 
                            (CPythonVarargsFunction_Delegate)
                            Marshal.GetDelegateForFunctionPointer(
                                thisMethod.ml_meth, 
                                typeof(CPythonVarargsFunction_Delegate));
                        break;
                
                    case METH.VARARGS | METH.KEYWORDS:
                        moduleCode.Append(String.Format(
                            "\ndef {0}(*args, **kwargs):\n  '''{1}'''\n  return _jumpy_dispatch_kwargs('{0}', args, kwargs)\n",
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
        
        public override int PyModule_AddObject(IntPtr modulePtr, string name, IntPtr itemPtr)
        {
        	if (this.RefCount(modulePtr) == 0)
        	{
        		return -1;
        	}
            EngineModule module = (EngineModule)this.Retrieve(modulePtr);
            if (this.RefCount(itemPtr) > 0)
            {
            	module.Globals[name] = this.Retrieve(itemPtr);
            	this.DecRef(itemPtr);
            }
            else
            {
            	IntPtr typePtr = CPyMarshal.Offset(
            		itemPtr, Marshal.OffsetOf(typeof(PyTypeObject), "ob_type"));
            	
            	if (CPyMarshal.ReadPtr(typePtr) == this.PyType_Type)
            	{
            		StringBuilder classCode = new StringBuilder();
            		classCode.Append(String.Format(
            			"class {0}(object):\n  pass", name));
            		this.engine.Execute(classCode.ToString(), module);
            		object klass = module.Globals[name];
            		this.ptrmap[itemPtr] = klass;
            	}
            }
            return 0;
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


        protected virtual Dictionary<int, object> 
        GetArgValues(IntPtr args)
        {
            Tuple actualArgs = (Tuple)this.Retrieve(args);
            Dictionary<int, object> result =  new Dictionary<int, object>();
            for (int i = 0; i < actualArgs.GetLength(); i++)
            {
                result[i] = actualArgs[i];
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


        protected virtual int 
        SetArgValues(Dictionary<int, object> argsToWrite, 
                     Dictionary<int, ArgWriter> argWriters, 
                     IntPtr outPtr)
        {
        	try
        	{
				foreach (KeyValuePair<int,object> p in argsToWrite)
				{
					argWriters[p.Key].Write(outPtr, p.Value);
				}
            }
            catch (Exception e)
            {
            	this._lastException = e;
            	return 0;
            }
            return 1;
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
            return this.SetArgValues(argsToWrite, argWriters, outPtr);
        }


        public override int 
        PyArg_ParseTuple(IntPtr args, 
					 	 string format, 
					 	 IntPtr outPtr)
        {
            Dictionary<int, object> argsToWrite = this.GetArgValues(args);
            Dictionary<int, ArgWriter> argWriters = this.GetArgWriters(format);
            return this.SetArgValues(argsToWrite, argWriters, outPtr);
        }
        
        
        private IntPtr 
        AllocPyString(int length)
        {
        	int size = Marshal.SizeOf(typeof(PyStringObject)) + length;
        	IntPtr data = this.allocator.Alloc(size);
        	
        	PyStringObject s = new PyStringObject();
        	s.ob_refcnt = 1;
        	s.ob_type = IntPtr.Zero;
        	s.ob_size = (uint)length;
        	s.ob_shash = -1;
        	s.ob_sstate = 0;
        	Marshal.StructureToPtr(s, data, false);
        	
        	IntPtr terminator = CPyMarshal.Offset(data, size - 1);
        	CPyMarshal.WriteByte(terminator, 0);
        
        	return data;
        }
        
        
        private IntPtr
        CreatePyStringWithBytes(byte[] bytes)
        {
        	IntPtr strPtr = this.AllocPyString(bytes.Length);
        	IntPtr bufPtr = CPyMarshal.Offset(
        		strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
        	Marshal.Copy(bytes, 0, bufPtr, bytes.Length);
        	
			char[] chars = Array.ConvertAll<byte, char>(
				bytes, new Converter<byte, char>(CharFromByte));
			this.ptrmap[strPtr] = new string(chars);
        	return strPtr;
        }
        
        
        public override IntPtr PyString_FromString(IntPtr stringData)
        {
        	// maybe I should just DllImport memcpy... :/
        	IntPtr current = stringData;
        	List<byte> bytesList = new List<byte>();
        	while (CPyMarshal.ReadByte(current) != 0)
        	{
        		bytesList.Add(CPyMarshal.ReadByte(current));
        		current = CPyMarshal.Offset(current, 1);
        	}
        	byte[] bytes = new byte[bytesList.Count];
        	bytesList.CopyTo(bytes);
        	return this.CreatePyStringWithBytes(bytes);
        }
        
        public override IntPtr
        PyString_FromStringAndSize(IntPtr stringData, int length)
        {
        	if (stringData == IntPtr.Zero)
        	{
        		IntPtr data = this.AllocPyString(length);
        		this.StoreUnmanagedData(data, UnmanagedDataMarker.PyStringObject);
        		return data;
        	}
        	else
        	{
        		byte[] bytes = new byte[length];
        		Marshal.Copy(stringData, bytes, 0, length);
        		return this.CreatePyStringWithBytes(bytes);
        	}
        }
        
        private int
        _PyString_Resize_Grow(IntPtr strPtrPtr, int newSize)
        {
        	IntPtr oldStr = CPyMarshal.ReadPtr(strPtrPtr);
			IntPtr newStr = IntPtr.Zero;
        	try
        	{
        		newStr = this.allocator.Realloc(
					oldStr, Marshal.SizeOf(typeof(PyStringObject)) + newSize);
        	}
        	catch (OutOfMemoryException e)
        	{
        		this._lastException = e;
        		this.Delete(oldStr);
        		return -1;
        	}
            this.ptrmap.Remove(oldStr);
        	CPyMarshal.WritePtr(strPtrPtr, newStr);
        	this.StoreUnmanagedData(newStr, UnmanagedDataMarker.PyStringObject);
        	return this._PyString_Resize_NoGrow(newStr, newSize);
        }
        
        private int
        _PyString_Resize_NoGrow(IntPtr strPtr, int newSize)
        {
        	IntPtr ob_sizePtr = CPyMarshal.Offset(
        		strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_size"));
        	CPyMarshal.WriteInt(ob_sizePtr, newSize);
        	IntPtr bufPtr = CPyMarshal.Offset(
        		strPtr, Marshal.OffsetOf(typeof(PyStringObject), "ob_sval"));
        	IntPtr terminatorPtr = CPyMarshal.Offset(
        		bufPtr, newSize);
        	CPyMarshal.WriteByte(terminatorPtr, 0);
        	return 0;
        }
        
        public override int
        _PyString_Resize(IntPtr strPtrPtr, int newSize)
        {
        	IntPtr strPtr = CPyMarshal.ReadPtr(strPtrPtr);
        	PyStringObject str = (PyStringObject)Marshal.PtrToStructure(strPtr, typeof(PyStringObject));
        	if (str.ob_size < newSize)
        	{
        		return this._PyString_Resize_Grow(strPtrPtr, newSize);
        	}
        	else
        	{
        		return this._PyString_Resize_NoGrow(strPtr, newSize);
        	}
        }
        
        
        
    }

}
