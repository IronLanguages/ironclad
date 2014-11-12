using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;

using IronPython.Hosting;
using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Hosting.Providers;
using Microsoft.Scripting.Runtime;

namespace Ironclad
{
    class DictionaryWrapper : IDictionary<string, object>
    {
        readonly IDictionary<object, object> inner;
        public DictionaryWrapper(IDictionary<object, object> wrapped)
        {
            this.inner = wrapped;
        }

        #region IDictionary<string,object> Members

        public void Add(string key, object value) { inner.Add(key, value); }
        public bool ContainsKey(string key) { return inner.ContainsKey(key); }
        public ICollection<string> Keys {
            get
            {
                var ret = new List<string>(inner.Count);
                foreach (var key in inner.Keys)
                {
                    ret.Add((string)key);
                }
                return ret;
            }
        }
        public bool Remove(string key) { return inner.Remove(key); }
        public bool TryGetValue(string key, out object value) { return inner.TryGetValue(key, out value); }
        public ICollection<object> Values { get { return inner.Values; } }

        public object this[string key]
        {
            get { return inner[key]; }
            set { inner[key] = value; }
        }

        #endregion

        #region ICollection<KeyValuePair<string,object>> Members

        public void Add(KeyValuePair<string, object> item) { inner.Add(item.Key, item.Value); }
        public void Clear() { inner.Clear(); }
        public bool Contains(KeyValuePair<string, object> item) {
            return inner.Contains(new KeyValuePair<object, object>(item.Key, item.Value)); }
        public void CopyTo(KeyValuePair<string, object>[] array, int arrayIndex) { throw new NotImplementedException(); }
        public int Count { get { return inner.Count; } }
        public bool IsReadOnly { get { return false; } }
        public bool Remove(KeyValuePair<string, object> item) { return inner.Remove(item.Key); }

        #endregion

        #region IEnumerable<KeyValuePair<string,object>> Members

        public IEnumerator<KeyValuePair<string, object>> GetEnumerator()
        {
            foreach (var item in inner)
            {
                yield return new KeyValuePair<string, object>((string)item.Key, item.Value);
            }
        }

        #endregion

        #region IEnumerable Members

        System.Collections.IEnumerator System.Collections.IEnumerable.GetEnumerator()
        {
            foreach (var item in inner)
            {
                yield return new KeyValuePair<string, object>((string)item.Key, item.Value);
            }
        }

        #endregion
    }

    public partial class PythonMapper : PythonApi
    {
        public override IntPtr 
        Py_InitModule4(string name, IntPtr methodsPtr, string doc, IntPtr selfPtr, int apiver)
        {
            name = this.FixImportName(name);
            
            PythonDictionary methodTable = new PythonDictionary();
            PythonModule module = new PythonModule();
            this.AddModule(name, module);
            this.CreateModulesContaining(name);

            PythonDictionary __dict__ = module.Get__dict__();
            __dict__["__doc__"] = doc;
            __dict__["__name__"] = name;
            string __file__ = this.importFiles.Peek();
            __dict__["__file__"] = __file__;
            List __path__ = new List();
            if (__file__ != null)
            {
                __path__.append(Path.GetDirectoryName(__file__));
            }
            __dict__["__path__"] = __path__;
            __dict__["_dispatcher"] = new Dispatcher(this, methodTable, selfPtr);

            StringBuilder moduleCode = new StringBuilder();
            moduleCode.Append(CodeSnippets.USEFUL_IMPORTS);
            CallableBuilder.GenerateFunctions(moduleCode, methodsPtr, methodTable);
            this.ExecInModule(moduleCode.ToString(), module);
            
            return this.Store(module);
        }
        
        public override IntPtr
        PyEval_GetBuiltins()
        {
            PythonModule __builtin__ = this.GetModule("__builtin__");
            return this.Store(__builtin__.Get__dict__());
        }
        
        public override IntPtr
        PySys_GetObject(string name)
        {
            try
            {
                return this.Store(this.python.SystemState.Get__dict__()[name]);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }

        public override IntPtr
        PyModule_New(string name)
        {
            PythonModule module = new PythonModule();
            module.Get__dict__()["__name__"] = name;
            module.Get__dict__()["__doc__"] = "";
            return this.Store(module);
        }

        public override IntPtr
        PyModule_GetDict(IntPtr modulePtr)
        {
            PythonModule module = (PythonModule)this.Retrieve(modulePtr);
            return this.Store(module.Get__dict__());
        }

        private int 
        IC_PyModule_Add(IntPtr modulePtr, string name, object value)
        {
            if (!this.map.HasPtr(modulePtr))
            {
                return -1;
            }
            PythonModule module = (PythonModule)this.Retrieve(modulePtr);
            module.__setattr__(scratchContext, name, value);
            return 0;
        }
        
        public override int 
        PyModule_AddObject(IntPtr modulePtr, string name, IntPtr valuePtr)
        {
            if (!this.map.HasPtr(modulePtr))
            {
                return -1;
            }
            object value = this.Retrieve(valuePtr);
            this.DecRef(valuePtr);
            return this.IC_PyModule_Add(modulePtr, name, value);
        }
        
        public override int
        PyModule_AddIntConstant(IntPtr modulePtr, string name, int value)
        {
            return this.IC_PyModule_Add(modulePtr, name, value);
        }
        
        public override int
        PyModule_AddStringConstant(IntPtr modulePtr, string name, string value)
        {
            return this.IC_PyModule_Add(modulePtr, name, value);
        }

        private void
        ExecInModule(string code, PythonModule module)
        {
            SourceUnit script = this.python.CreateSnippet(code, SourceCodeKind.Statements);
            script.Execute(new Scope(new DictionaryWrapper((IDictionary<object, object>)module.Get__dict__())));
        }
        
        public void
        AddModule(string name, PythonModule module)
        {
            PythonDictionary modules = (PythonDictionary)this.python.SystemState.Get__dict__()["modules"];
            modules[name] = module;
        }

        public PythonModule
        GetModule(string name)
        {
            PythonDictionary modules = (PythonDictionary)this.python.SystemState.Get__dict__()["modules"];
            if (modules.has_key(name))
            {
                return (PythonModule)modules[name];
            }
            return null;
        }

        public void
        LoadModule(string path, string name)
        {
            this.EnsureGIL();
            this.importNames.Push(name);
            this.importFiles.Push(path);

            string dir = Path.GetDirectoryName(path);
            string library = Path.GetFileName(path);
            string previousDir = Environment.CurrentDirectory;

            Environment.CurrentDirectory = dir;
            try
            {
                this.importer.Load(library);
            }
            finally
            {
                Environment.CurrentDirectory = previousDir;
                this.importNames.Pop();
                this.importFiles.Pop();
                this.ReleaseGIL();
            }
        }

        private PythonModule
        CreateModule(string name)
        {
            PythonModule module = this.GetModule(name);
            if (module == null)
            {
                module = new PythonModule();
                module.Get__dict__()["__name__"] = name;
                this.AddModule(name, module);
            }
            return module;
        }

        private void
        CreateModulesContaining(string name)
        {
            PythonModule inner = this.CreateModule(name);
            int lastDot = name.LastIndexOf('.');
            if (lastDot != -1)
            {
                this.CreateModulesContaining(name.Substring(0, lastDot));
                PythonModule outer = this.GetModule(name.Substring(0, lastDot));
                outer.Get__dict__()[name.Substring(lastDot + 1)] = inner;
            }
        }
        
        private void
        CreateScratchModule()
        {
            this.scratchModule = new PythonModule();
            this.scratchModule.Get__dict__()["_mapper"] = this;

            this.ExecInModule(CodeSnippets.USEFUL_IMPORTS, this.scratchModule);
            this.scratchContext = new ModuleContext(this.scratchModule.Get__dict__(), this.python).GlobalContext;
        }
    }
}
