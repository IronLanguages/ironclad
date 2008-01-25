using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

using IronPython.Hosting;

namespace JumPy
{

    public class Python25Mapper : PythonMapper
    {
        private PythonEngine engine;
        
        public Python25Mapper(PythonEngine eng)
        {
            this.engine = eng;
        }
        
        public override IntPtr Py_InitModule4(string name, IntPtr methods, string doc, IntPtr self, int apiver)
        {
            Dictionary<string, object> globals = new Dictionary<string, object>();
            globals["__doc__"] = doc;
            
            IntPtr methodPtr = methods;
            StringBuilder moduleCode = new StringBuilder();
            while (Marshal.ReadInt32(methodPtr) != 0)
            {
                PyMethodDef thisMethod = (PyMethodDef)Marshal.PtrToStructure(methodPtr, typeof(PyMethodDef));
                moduleCode.Append(String.Format("\ndef {0}(*args):\n  '''{1}'''\n  pass\n",
                                                thisMethod.ml_name, thisMethod.ml_doc));
                methodPtr = (IntPtr)(methodPtr.ToInt32() + Marshal.SizeOf(typeof(PyMethodDef)));
            }
            
            EngineModule module = this.engine.CreateModule(name, globals, true);
            this.engine.Execute(moduleCode.ToString(), module);
            return IntPtr.Zero;
        }
    }


}