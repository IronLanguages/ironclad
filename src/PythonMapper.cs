using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

namespace JumPy
{

    public class PythonMapper
    {
        private Dictionary<string, Delegate> map = new Dictionary<string, Delegate>();
    
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr Py_InitModule4_Delegate(string name, IntPtr methods, string doc, IntPtr self, int apiver);
        public virtual IntPtr Py_InitModule4(string name, IntPtr methods, string doc, IntPtr self, int apiver)
        {
            return IntPtr.Zero;
        }
        
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr PyString_FromString_Delegate(string text);
        public virtual IntPtr PyString_FromString(string text)
        {
            return IntPtr.Zero;
        }
        
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr PyString_FromStringAndSize_Delegate(IntPtr stringPtr, int size);
        public virtual IntPtr PyString_FromStringAndSize(IntPtr stringPtr, int size)
        {
            return IntPtr.Zero;
        }
        
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate int _PyString_Resize_Delegate(IntPtr stringPtrPtr, int size);
        public virtual int _PyString_Resize(IntPtr stringPtrPtr, int size)
        {
            return -1;
        }
        
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate int PyModule_AddObject_Delegate(IntPtr module, string name, IntPtr item);
        public virtual int PyModule_AddObject(IntPtr module, string name, IntPtr item)
        {
            return 0;
        }
        
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate int PyArg_ParseTupleAndKeywords_Delegate(IntPtr args, IntPtr kwargs, string format, IntPtr kwlist, IntPtr argPtr);
        public virtual int PyArg_ParseTupleAndKeywords(IntPtr args, IntPtr kwargs, string format, IntPtr kwlist, IntPtr argPtr)
        {
            return 0;
        }
        
        
		        
		[UnmanagedFunctionPointer(CallingConvention.Cdecl)]
		public delegate IntPtr PyEval_SaveThread_Delegate();
		public virtual IntPtr PyEval_SaveThread()
		{
			return IntPtr.Zero;
        }
        
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate void PyEval_RestoreThread_Delegate(IntPtr _);
        public virtual void PyEval_RestoreThread(IntPtr _)
        {
            ;
        }
        
        
        
        
        public IntPtr GetAddress(string name)
        {
            if (this.map.ContainsKey(name))
            {
                return Marshal.GetFunctionPointerForDelegate(this.map[name]);
            }
        
            switch (name)
            {
                case "Py_InitModule4":
                    this.map[name] = new Py_InitModule4_Delegate(this.Py_InitModule4);
                    break;
                case "PyString_FromString":
                    this.map[name] = new PyString_FromString_Delegate(this.PyString_FromString);
                    break;
                case "PyString_FromStringAndSize":
                    this.map[name] = new PyString_FromStringAndSize_Delegate(this.PyString_FromStringAndSize);
                    break;
                case "_PyString_Resize":
                    this.map[name] = new _PyString_Resize_Delegate(this._PyString_Resize);
                    break;
                case "PyModule_AddObject":
                    this.map[name] = new PyModule_AddObject_Delegate(this.PyModule_AddObject);
                    break;
                case "PyArg_ParseTupleAndKeywords":
                    this.map[name] = new PyArg_ParseTupleAndKeywords_Delegate(this.PyArg_ParseTupleAndKeywords);
                    break;
            
            	case "PyEval_SaveThread":
                    this.map[name] = new PyEval_SaveThread_Delegate(this.PyEval_SaveThread);
                    break;
            	case "PyEval_RestoreThread":
                    this.map[name] = new PyEval_RestoreThread_Delegate(this.PyEval_RestoreThread);
                    break;
            
                default:
                    return IntPtr.Zero;
            }
            return Marshal.GetFunctionPointerForDelegate(this.map[name]);
        }
        
        
        public virtual void Fill_PyString_Type(IntPtr address)
        {
            ;
        }
        
        
        public void SetData(string name, IntPtr address)
        {
            switch (name)
            {
                case "PyString_Type":
                    this.Fill_PyString_Type(address);
                    break;
            }
        }
    }


}