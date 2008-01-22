using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
using IronPython.Hosting;
using IronPython.Runtime;
using IronPython.Runtime.Calls;
using IronPython.Runtime.Types;

namespace JumPy
{
    public class FakePython24
    {
        #region Infrastructure
        [DllImport(".\\python24.dll")]
        private static extern void init(IntPtr func_getter);

        public delegate IntPtr FakePyCFunction_Delegate(IntPtr self, IntPtr args);

        private Bridge bridge;
        private FunctionPointerStore fpStore;
 
        public FakePython24(PythonEngine eng)
        {
            this.bridge = new Bridge(eng);
            this.fpStore = new FunctionPointerStore();
            this.fpStore.Add(
                "GetFunctionPointer",
                new GetFunctionPointer_Delegate(this.GetFunctionPointer));
            
            Console.WriteLine("FakePython24: loading fake python24.dll...");
            init(this.fpStore.Get("GetFunctionPointer"));
            Console.WriteLine("FakePython24: loaded");
        }

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr GetFunctionPointer_Delegate(string name);
        public IntPtr GetFunctionPointer(string name)
        {
            if (!this.fpStore.Has(name))
            {
                bool found = true;
                switch (name)
                {
                    case "Py_InitModule4":
                        this.fpStore.Add(
                            name,
                            new Py_InitModule4_Delegate(this.Py_InitModule4));
                        break;

                    case "PyModule_AddObject":
                        this.fpStore.Add(
                            name,
                            new PyModule_AddObject_Delegate(this.PyModule_AddObject));
                        break;
                    case "PyModule_AddIntConstant":
                        this.fpStore.Add(
                            name,
                            new PyModule_AddIntConstant_Delegate(this.PyModule_AddIntConstant));
                        break;
                    case "PyModule_AddStringConstant":
                        this.fpStore.Add(
                            name,
                            new PyModule_AddStringConstant_Delegate(this.PyModule_AddStringConstant));
                        break;

                    case "PyErr_Format":
                        this.fpStore.Add(
                            name,
                            new PyErr_Format_Delegate(this.PyErr_Format));
                        break;
                    case "PyErr_NewException":
                        this.fpStore.Add(
                            name,
                            new PyErr_NewException_Delegate(this.PyErr_NewException));
                        break;
                    case "PyErr_Occurred":
                        this.fpStore.Add(
                            name,
                            new PyErr_Occurred_Delegate(this.PyErr_Occurred));
                        break;
                    case "PyErr_SetObject":
                        this.fpStore.Add(
                            name,
                            new PyErr_SetObject_Delegate(this.PyErr_SetObject));
                        break;
                    case "PyErr_SetString":
                        this.fpStore.Add(
                            name,
                            new PyErr_SetString_Delegate(this.PyErr_SetString));
                        break;

                    case "PyString_FromString":
                        this.fpStore.Add(
                            name,
                            new PyString_FromString_Delegate(this.PyString_FromString));
                        break;
                    case "PyString_FromStringAndSize":
                        this.fpStore.Add(
                            name,
                            new PyString_FromStringAndSize_Delegate(this.PyString_FromStringAndSize));
                        break;
                    case "_PyString_Resize":
                        this.fpStore.Add(
                            name,
                            new _PyString_Resize_Delegate(this._PyString_Resize));
                        break;

                    case "PyArg_ParseTuple":
                        this.fpStore.Add(
                            name,
                            new PyArg_ParseTuple_Delegate(this.PyArg_ParseTuple));
                        break;

                    case "PyInt_FromLong":
                        this.fpStore.Add(
                            name,
                            new PyInt_FromLong_Delegate(this.PyInt_FromLong));
                        break;

                    case "PyEval_SaveThread":
                        this.fpStore.Add(
                            name,
                            new PyEval_SaveThread_Delegate(this.PyEval_SaveThread));
                        break;
                    case "PyEval_RestoreThread":
                        this.fpStore.Add(
                            name,
                            new PyEval_RestoreThread_Delegate(this.PyEval_RestoreThread));
                        break;
                    case "PyThread_allocate_lock":
                        this.fpStore.Add(
                            name,
                            new PyThread_allocate_lock_Delegate(this.PyThread_allocate_lock));
                        break;

                    default:
                        found = false;
                        break;
                }
                if (found)
                {
                    Console.WriteLine(String.Format(
                        "FakePython24: registering {0:s}", name));
                }
            }
            return this.fpStore.Get(name);
        }
        #endregion

        #region PyModule... functions
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr Py_InitModule4_Delegate(string name, IntPtr methods, string doc, IntPtr self, int apiver);
        public IntPtr Py_InitModule4(string name, IntPtr methods, string doc, IntPtr self, int apiver)
        {
            //Console.WriteLine(String.Format("FakePython24: Py_InitModule4: {0:s} {1:d}\n", name, apiver));
            StringBuilder moduleBuilder = new StringBuilder();
            moduleBuilder.Append("from System import IntPtr\n");
            moduleBuilder.Append("from System.Runtime.InteropServices import Marshal\n\n");
            moduleBuilder.Append(
                "def __dispatch(funcName, *args):\n" +
                "    print funcName, args\n" +
                "    try:\n" +
                "        #fixme - args will be leaked - possibly just decref in finally?\n" +
                "        result = __funcMap[funcName](IntPtr.Zero, __bridge.Remember(args))\n" +
                "    except Exception, e:\n"+
                "        print '__dispatch failed:\\n\\n%s\\n' % e.clsException\n"+
                "        raise\n"+
                "    if __bridge.Contains(result):\n"+
                "        return __bridge.Retrieve(result)\n" +
                "    error = __bridge.ExceptionType\n" +
                "    info = __bridge.ExceptionInfo\n" +
                "    __bridge.ClearException()\n" +
                "    raise error(info)\n");
            
            IntPtr nextMethod = methods;
            Dictionary<String, Delegate> funcMap = new Dictionary<string, Delegate>();
            while (Marshal.ReadInt32(nextMethod) != 0)
            {
                // fixme - currently assuming ml_meth is METH.VARARGS (no kwargs)
                PyMethodDef thisMethod = (PyMethodDef)Marshal.PtrToStructure(nextMethod, typeof(PyMethodDef));
                funcMap[thisMethod.ml_name] = Marshal.GetDelegateForFunctionPointer(thisMethod.ml_meth, typeof(FakePyCFunction_Delegate));
                moduleBuilder.Append(String.Format("def {0:s}(*args):\n", thisMethod.ml_name));
                moduleBuilder.Append(String.Format("    '''{0:s}'''\n", thisMethod.ml_doc));
                moduleBuilder.Append(String.Format("    return __dispatch('{0:s}', *args)\n\n", thisMethod.ml_name));
                nextMethod = (IntPtr)((uint)nextMethod + 16);
            }

            Dictionary<string, object> globals = new Dictionary<string, object>();
            globals["__doc__"] = doc;
            globals["__bridge"] = this.bridge;
            globals["__funcMap"] = funcMap;
            return this.bridge.CreateModule(name, moduleBuilder.ToString(), globals);
        }
        
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate int PyModule_AddObject_Delegate(IntPtr module, string name, IntPtr obj);
        public int PyModule_AddObject(IntPtr module, string name, IntPtr obj)
        {
            this.bridge.AddMappedItemToModule(module, name, obj);
            return 0;
        }
        
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate int PyModule_AddIntConstant_Delegate(IntPtr module, string name, int value);
        public int PyModule_AddIntConstant(IntPtr module, string name, int value)
        {
            this.bridge.AddSimpleItemToModule(module, name, value);
            return 0;
        }

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate int PyModule_AddStringConstant_Delegate(IntPtr module, string name, string value);
        public int PyModule_AddStringConstant(IntPtr module, string name, string value)
        {   
            this.bridge.AddSimpleItemToModule(module, name, value);
            return 0;
        }
        #endregion

        #region PyString... functions
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr PyString_FromString_Delegate(string str);
        public IntPtr PyString_FromString(string str)
        {
            //Console.WriteLine("FakePython24: PyString_FromString");
            return this.bridge.CreateString(str);
        }

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr PyString_FromStringAndSize_Delegate(IntPtr srcAddr, int size);
        public IntPtr PyString_FromStringAndSize(IntPtr srcAddr, int size)
        {
            //Console.WriteLine("FakePython24: PyString_FromStringAndSize");
            byte[] str = new byte[size];
            if (srcAddr != IntPtr.Zero)
            {
                for (int i = 0; i < size; ++i)
                {
                    str[i] = Marshal.ReadByte(srcAddr, i);
                }
            }
            else
            {
                for (int i = 0; i < size; ++i)
                {
                    str[i] = 0;
                }
            }
            return this.bridge.CreateStringFromBytes(str);
        }

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate int _PyString_Resize_Delegate(IntPtr pyStr, int newsize);
        public int _PyString_Resize(IntPtr pyStr, int newsize)
        {
            Console.WriteLine("FakePython24: _PyString_Resize:\n if you can read this message, it appears we have a tolerable string implementation. huzzah!");
            return 0;
        }
        #endregion

        #region PyErr... functions

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr PyErr_NewException_Delegate(string name, IntPtr _base, IntPtr dict);
        public IntPtr PyErr_NewException(string name, IntPtr _base, IntPtr dict)
        {
            IntPtr result = this.bridge.CreateException(name);
            return result;
        }

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr PyErr_Format_Delegate(IntPtr excType, string format);
        public IntPtr PyErr_Format(IntPtr excType, string message)
        {
            // we do the message formatting in cpp, to avoid melted brains
            this.bridge.SetException(excType, message);
            return IntPtr.Zero;
        }
        
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate void PyErr_SetObject_Delegate(IntPtr type, IntPtr value);
        public void PyErr_SetObject(IntPtr excType, IntPtr value)
        {
            Console.WriteLine("FakePython24: PyErr_SetObject: not really implemented");
            this.bridge.SetException(excType, "some object");
        }

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate void PyErr_SetString_Delegate(IntPtr type, string message);
        public void PyErr_SetString(IntPtr excType, string message)
        {
            this.bridge.SetException(excType, message);
        }

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate void PyErr_Print_Delegate();
        public void PyErr_Print()
        {
            Console.WriteLine("FakePython24: PyErr_Print: pretend this is a traceback");
            this.bridge.ClearException();
        }

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr PyErr_Occurred_Delegate();
        public IntPtr PyErr_Occurred()
        {
            return this.bridge.CExceptionType;
        }
        #endregion

        #region PyArg... functions
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate int PyArg_ParseTuple_Delegate(IntPtr args, string format, IntPtr stuff);
        public int PyArg_ParseTuple(IntPtr args, string format, IntPtr argAddrs)
        {
            //Console.WriteLine("FakePython24: PyArg_ParseTuple");
            Tuple actualArgs = (Tuple)this.bridge.Retrieve(args);

            IntPtr addrToWrite = IntPtr.Zero;
            IntPtr nextArgAddr = argAddrs;
            int nextArgIndex = 0;
            int nextFormatChar = 0;
            bool optional = false;

            while (Marshal.ReadIntPtr(nextArgAddr) != IntPtr.Zero)
            {
                if (optional && nextArgIndex >= actualArgs.Count)
                {
                    //Console.WriteLine("early return after {0} args", nextArgIndex);
                    return nextArgIndex;
                }

                bool advancePtr = true;
                char formatChar = format[nextFormatChar];
                addrToWrite = Marshal.ReadIntPtr(nextArgAddr);
                switch (formatChar)
                {
                    case '|':
                        optional = true;
                        advancePtr = false;
                        break;

                    case 'k':
                    case 'l':
                        Marshal.WriteInt32(addrToWrite, (int)(actualArgs[nextArgIndex]));
                        break;

                    case 's':
                        // fixme - leak
                        IntPtr cStringAddr = Marshal.StringToCoTaskMemAnsi((string)actualArgs[nextArgIndex]);
                        Marshal.WriteIntPtr(addrToWrite, cStringAddr);

                        if (format[nextFormatChar + 1] == '#')
                        {
                            nextFormatChar += 1;
                            nextArgAddr = (IntPtr)((uint)nextArgAddr + 4);
                            addrToWrite = Marshal.ReadIntPtr(nextArgAddr);
                            Marshal.WriteInt32(addrToWrite, ((string)(actualArgs[nextArgIndex])).Length);
                        }
                        break;

                    case ':':
                        return nextArgIndex;
                }
                nextFormatChar += 1;
                if (advancePtr)
                {
                    nextArgIndex += 1;
                    nextArgAddr = (IntPtr)((uint)nextArgAddr + 4);
                }
            }
            //Console.WriteLine("return after {0} args", nextArgIndex);
            return nextArgIndex;
        }
        #endregion

        #region PyInt... functions
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr PyInt_FromLong_Delegate(int value);
        public IntPtr PyInt_FromLong(int value)
        {
            return this.bridge.CreateInt(value);
        }
        #endregion

        #region empty Py... functions
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate void Py_Initialize_Delegate();
        private void Py_Initialize()
        {
            //Console.WriteLine("FakePython24: Py_Initialize()");
        }

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr PyEval_SaveThread_Delegate();
        public IntPtr PyEval_SaveThread()
        {
            // fixme - probably can't actually ignore, unless extension library is typesafe
            return IntPtr.Zero;
        }

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate void PyEval_RestoreThread_Delegate(IntPtr thread);
        public void PyEval_RestoreThread(IntPtr thread)
        {
            // fixme - probably can't actually ignore, unless extension library is typesafe
        }
        
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr PyThread_allocate_lock_Delegate();
        public IntPtr PyThread_allocate_lock()
        {
            // fixme - probably can't actually ignore
            return IntPtr.Zero;
        }
        #endregion
    }
}
