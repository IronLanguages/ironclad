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

    class Bridge
    {
        public Bridge(PythonEngine eng)
        {
            this.engine = eng;
            this.map = new Dictionary<IntPtr, object>();
            this.exceptionType = IntPtr.Zero;
            this.exceptionInfo = null;
        }

        #region Utility
        public IntPtr Remember(object obj)
        {
            return this._AddItem(this._CreateEmptyCItem(), obj);
        }

        public object Retrieve(IntPtr objKey)
        {
            return this.map[objKey];
        }

        public bool Contains(IntPtr objKey)
        {
            return this.map.ContainsKey(objKey);
        }

        public void CollectGarbage()
        {
            // fixme - no idea whether this will actually work as intended.
            List<IntPtr> garbage = new List<IntPtr>();
            foreach (IntPtr k in this.map.Keys)
            {
                // fixme - to avoid dereferencing ob_type, which is always IntPtr.Zero at the moment,
                // we create everything with a refcount of 2 (not 1) and consider them to be dead 
                // when refcount hits 1 (not 0)
                if (Marshal.ReadInt32(k) == 1)
                {
                    garbage.Add(k);
                }
            }
            foreach (IntPtr g in garbage)
            {
                this.map.Remove(g);
            }
        }
        #endregion

        #region Bridging methods
        public void AddSimpleItemToModule(IntPtr moduleKey, string name, object item)
        {
            EngineModule module = (EngineModule)this.map[moduleKey];
            module.Globals.Add(name, item);
        }

        public void AddMappedItemToModule(IntPtr moduleKey, string name, IntPtr itemKey)
        {
            EngineModule module = (EngineModule)this.map[moduleKey];
            module.Globals.Add(name, this.map[itemKey]);
        }

        public IntPtr CreateInt(int value)
        {
            return this._AddItem(this._CreatePyInt(value), value);
        }

        public IntPtr CreateString(string str)
        {
            return this._AddItem(this._CreatePyString(str), str);
        }

        public IntPtr CreateStringFromBytes(byte[] str)
        {
            return this._AddItem(this._CreatePyStringFromBytes(str), Encoding.UTF7.GetString(str, 0, str.Length));
        }

        public IntPtr CreateModule(string name, string moduleBuilder, Dictionary<string, object> globals)
        {
            EngineModule newModule = this.engine.CreateModule(name, globals, true);
            this.engine.Execute(moduleBuilder, newModule);
            return this.Remember(newModule);
        }

        public IntPtr CreateException(string name)
        {
            // fixme - would be nice to force the new exception class into the right module somehow
            string excClassName = "DirtyHackException";
            this.engine.Execute(String.Format(
                "class {0}(Exception):\n    pass\n{0}.__name__=\"{1}\"\n", excClassName, name));
            return this.Remember(this.engine.Evaluate(excClassName));
        }
        #endregion

        #region Error marshalling
        public void SetException(IntPtr excType, object excInfo)
        {
            if (this.Contains(excType))
            {
                this.exceptionType = excType;
            }
            else
            {
                this.exceptionType = IntPtr.Zero;
            }
            this.exceptionInfo = excInfo;
        }

        public void ClearException()
        {
            this.exceptionType = IntPtr.Zero;
            this.exceptionInfo = null;
        }

        public object ExceptionType
        {
            get
            {
                if (this.exceptionType != IntPtr.Zero)
                {
                    return this.Retrieve(this.exceptionType);

                }
                else
                {
                    return typeof(Exception);
                }
            }
        }

        public IntPtr CExceptionType
        {
            get
            {
                return this.exceptionType;
            }
        }

        public object ExceptionInfo
        {
            get
            {
                return this.exceptionInfo;
            }
        }

        #endregion

        #region Implementation details
        // 'struct' containing refcount and nothing else: macros accessing other fields will 
        // fail hideously.
        const int EMPTY_CPYTHON_OBJ_SIZE = 4;

        private PythonEngine engine;
        private Dictionary<IntPtr, object> map;
        private IntPtr exceptionType;
        private object exceptionInfo;

        private IntPtr _AddItem(IntPtr cItem, object mgdItem)
        {
            this.map[cItem] = mgdItem;
            return cItem;
        }

        private IntPtr _CreateEmptyCItem()
        {
            IntPtr ptr = Marshal.AllocHGlobal(EMPTY_CPYTHON_OBJ_SIZE);
            Marshal.WriteInt32(ptr, 2); // fixme - see CollectGarbage
            return ptr;
        }

        // fixme - next 2 methods identical apart from signature
        private IntPtr _CreatePyString(string str)
        {
            //Console.WriteLine(String.Format("Bridge._CreatePyString(): length {0}", str.Length));
            IntPtr ptr = Marshal.AllocHGlobal(21 + str.Length);

            PyStringHead strHead = new PyStringHead();
            strHead.ob_refcnt = 2; // fixme - see CollectGarbage
            strHead.ob_type = IntPtr.Zero; // fixme - definitely wrong
            strHead.ob_size = (UInt32)str.Length;
            strHead.ob_shash = -1; // will this ever be used, I wonder?
            strHead.ob_sstate = 0; // will this ever be used, I wonder?

            Marshal.StructureToPtr(strHead, ptr, false);
            for (int i = 0; i < str.Length; ++i)
            {
                Marshal.WriteByte(ptr, 20 + i, (byte)str[i]);
            }
            Marshal.WriteByte(ptr, 20 + str.Length, 0);
            //Console.WriteLine(String.Format("Bridge._CreatePyString(): allocated {0} bytes at {1:X}", 21 + str.Length, ptr));
            return ptr;
        }

        private IntPtr _CreatePyStringFromBytes(byte[] str)
        {
            // Console.WriteLine(String.Format("Bridge._CreatePyStringFromBytes(): length {0}", str.Length));
            IntPtr ptr = Marshal.AllocHGlobal(21 + str.Length);

            PyStringHead strHead = new PyStringHead();
            strHead.ob_refcnt = 2; // fixme - see CollectGarbage
            strHead.ob_type = IntPtr.Zero; // fixme - definitely wrong
            strHead.ob_size = (UInt32)str.Length;
            strHead.ob_shash = -1; // will this ever be used, I wonder?
            strHead.ob_sstate = 0; // will this ever be used, I wonder?

            Marshal.StructureToPtr(strHead, ptr, false);
            for (int i = 0; i < str.Length; ++i)
            {
                Marshal.WriteByte(ptr, 20 + i, (byte)str[i]);
            }
            Marshal.WriteByte(ptr, 20 + str.Length, 0);
            //Console.WriteLine(String.Format("Bridge._CreatePyStringFromBytes(): allocated {0} bytes at {1:X}", 21 + str.Length, ptr));
            return ptr;
        }

        private IntPtr _CreatePyInt(int value)
        {
            IntPtr ptr = Marshal.AllocHGlobal(12);

            PyInt pyInt = new PyInt();
            pyInt.ob_refcnt = 2; // fixme - see CollectGarbage
            pyInt.ob_type = IntPtr.Zero; // fixme - definitely wrong
            pyInt.ob_ival = value;

            // fixme - is false a memory leak in this case? don't understand docs...
            Marshal.StructureToPtr(pyInt, ptr, false);
            return ptr;
        }
        #endregion
    }
}
