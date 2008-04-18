using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

using IronPython.Hosting;
using IronPython.Runtime.Types;

using Ironclad.Structs;

using DispatchTable = System.Collections.Generic.Dictionary<string, System.Delegate>;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        private void
        GenerateMethods(StringBuilder code, 
                        IntPtr methods, 
                        DispatchTable methodTable,
                        string tablePrefix, 
                        string noargsTemplate,
                        string objargTemplate, 
                        string varargsTemplate, 
                        string varargsKwargsTemplate)
        {
            IntPtr methodPtr = methods;
            if (methodPtr == IntPtr.Zero)
            {
                return;
            }
            while (CPyMarshal.ReadInt(methodPtr) != 0)
            {
                PyMethodDef thisMethod = (PyMethodDef)Marshal.PtrToStructure(
                    methodPtr, typeof(PyMethodDef));
                
                string template = null;
                Delegate dgt = null;
                
                bool unsupportedFlags = false;
                switch (thisMethod.ml_flags)
                {
                    case METH.NOARGS:
                        template = noargsTemplate;
                        dgt = (CPythonVarargsFunction_Delegate)
                            Marshal.GetDelegateForFunctionPointer(
                                thisMethod.ml_meth, 
                                typeof(CPythonVarargsFunction_Delegate));
                        break;
                        
                    case METH.O:
                        template = objargTemplate;
                        dgt = (CPythonVarargsFunction_Delegate)
                            Marshal.GetDelegateForFunctionPointer(
                                thisMethod.ml_meth, 
                                typeof(CPythonVarargsFunction_Delegate));
                        break;
                        
                    case METH.VARARGS:
                        template = varargsTemplate;
                        dgt = (CPythonVarargsFunction_Delegate)
                            Marshal.GetDelegateForFunctionPointer(
                                thisMethod.ml_meth, 
                                typeof(CPythonVarargsFunction_Delegate));
                        break;
                        
                    case METH.VARARGS | METH.KEYWORDS:
                        template = varargsKwargsTemplate;
                        dgt = (CPythonVarargsKwargsFunction_Delegate)
                            Marshal.GetDelegateForFunctionPointer(
                                thisMethod.ml_meth, 
                                typeof(CPythonVarargsKwargsFunction_Delegate));
                        break;
                        
                    default:
                        unsupportedFlags = true;
                        break;
                }
                
                if (!unsupportedFlags)
                {
                    code.Append(String.Format(template,
                        thisMethod.ml_name, thisMethod.ml_doc, tablePrefix));
                    methodTable[tablePrefix + thisMethod.ml_name] = dgt;
                }
                else
                {
                    Console.WriteLine("Detected unsupported method flags for {0}{1}; ignoring.",
                        tablePrefix, thisMethod.ml_name);
                }
                
                methodPtr = (IntPtr)(methodPtr.ToInt32() + Marshal.SizeOf(typeof(PyMethodDef)));
            }
        }
        
        
        public override IntPtr 
        Py_InitModule4(string name, IntPtr methods, string doc, IntPtr self, int apiver)
        {
            Dictionary<string, object> globals = new Dictionary<string, object>();
            globals["_ironclad_mapper"] = this;
            globals["__doc__"] = doc;
            
            DispatchTable methodTable = new DispatchTable();
            globals["_ironclad_dispatch_table"] = methodTable;
            
            StringBuilder moduleCode = new StringBuilder();
            moduleCode.Append(MODULE_CODE);
            
            this.GenerateMethods(
                moduleCode, 
                methods, 
                methodTable, 
                "", 
                NOARGS_FUNCTION_CODE, 
                OBJARG_FUNCTION_CODE,
                VARARGS_FUNCTION_CODE, 
                VARARGS_KWARGS_FUNCTION_CODE
            );
            
            EngineModule module = this.engine.CreateModule(name, globals, true);
            this.engine.Execute(moduleCode.ToString(), module);
            return this.Store(module);
        }
        
        
        
        private void
        GenerateClass(EngineModule module, string name, IntPtr typePtr)
        {
            StringBuilder classCode = new StringBuilder();
            
            IntPtr tp_namePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_name");
            string tp_name = Marshal.PtrToStringAnsi(tp_namePtr);
            
            string __name__ = tp_name;
            string __module__ = "";
            int lastDot = tp_name.LastIndexOf('.');
            if (lastDot != -1)
            {
                __name__ = tp_name.Substring(lastDot + 1);  
                __module__ = tp_name.Substring(0, lastDot);
            }
            
            string __doc__ = "";
            IntPtr tp_docPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_doc");
            if (tp_docPtr != IntPtr.Zero)
            {
                __doc__ = Marshal.PtrToStringAnsi(tp_docPtr).Replace("\\", "\\\\");
            }
            classCode.Append(String.Format(CLASS_CODE, name, __module__, __doc__));
            
            IntPtr methodsPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_methods");
            if (methodsPtr != IntPtr.Zero)
            {
                this.GenerateMethods(
                    classCode, 
                    methodsPtr, 
                    (DispatchTable)module.Globals["_ironclad_dispatch_table"],
                    name + ".", 
                    NOARGS_METHOD_CODE, 
                    OBJARG_METHOD_CODE,
                    VARARGS_METHOD_CODE, 
                    VARARGS_KWARGS_METHOD_CODE
                );
            }
            
            Py_TPFLAGS tp_flags = (Py_TPFLAGS)CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), "tp_flags");
            if ((tp_flags & Py_TPFLAGS.HAVE_ITER) != 0)
            {
                if (CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_iter") != IntPtr.Zero)
                {
                    classCode.Append(String.Format(ITER_METHOD_CODE, "__iter__", "tp_iter"));
                }
                if (CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_iternext") != IntPtr.Zero)
                {
                    classCode.Append(String.Format(ITER_METHOD_CODE, "next", "tp_iternext"));
                }
            }
            
            classCode.Append(String.Format(CLASS_FIXUP_CODE, name, __name__));
            this.engine.Execute(classCode.ToString(), module);
            object klass = module.Globals[name];
            
            DynamicType.SetAttrMethod(klass, "_typePtr", typePtr);
            
            this.SetClassDelegateSlot(klass, typePtr, "tp_new", typeof(PyType_GenericNew_Delegate));
            this.SetClassDelegateSlot(klass, typePtr, "tp_init", typeof(CPython_initproc_Delegate));
            if ((tp_flags & Py_TPFLAGS.HAVE_ITER) != 0)
            {
                if (CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_iter") != IntPtr.Zero)
                {
                    this.SetClassDelegateSlot(klass, typePtr, "tp_iter", typeof(PyObject_GetIter_Delegate));
                }
                if (CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_iternext") != IntPtr.Zero)
                {
                    this.SetClassDelegateSlot(klass, typePtr, "tp_iternext", typeof(PyIter_Next_Delegate));
                }
            }
            this.StoreUnmanagedData(typePtr, klass);
        }
        
        
        public IntPtr ReturnAString(IntPtr ignored)
        {
            return this.Store("hello, I am the string you have been looking for");
        }
        
        
        private void SetClassDelegateSlot(object klass, IntPtr typePtr, string fieldName, Type delegateType)
        {
            Delegate dgt = CPyMarshal.ReadFunctionPtrField(typePtr, typeof(PyTypeObject), fieldName, delegateType);
            string attrName = String.Format("_{0}Dgt", fieldName);
            DynamicType.SetAttrMethod(klass, attrName, dgt);
        }
        
        
        public override int 
        PyModule_AddObject(IntPtr modulePtr, string name, IntPtr itemPtr)
        {
            if (!this.ptrmap.ContainsKey(modulePtr))
            {
                return -1;
            }
            EngineModule module = (EngineModule)this.Retrieve(modulePtr);
            if (this.ptrmap.ContainsKey(itemPtr))
            {
                module.Globals[name] = this.Retrieve(itemPtr);
                this.DecRef(itemPtr);
            }
            else
            {
                IntPtr typePtr = CPyMarshal.ReadPtrField(itemPtr, typeof(PyTypeObject), "ob_type");
                if (typePtr == this.PyType_Type)
                {
                    this.GenerateClass(module, name, itemPtr);
                }
            }
            return 0;
        }
    }
}