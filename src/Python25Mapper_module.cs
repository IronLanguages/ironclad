using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

using IronPython.Hosting;
using IronPython.Runtime.Types;

using JumPy.Structs;

using DispatchTable = System.Collections.Generic.Dictionary<string, System.Delegate>;

namespace JumPy
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
            globals["_jumpy_mapper"] = this;
            globals["__doc__"] = doc;
            
            DispatchTable methodTable = new DispatchTable();
            globals["_jumpy_dispatch_table"] = methodTable;
            
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
            
            IntPtr tp_namePtr = CPyMarshal.Offset(
                typePtr, Marshal.OffsetOf(typeof(PyTypeObject), "tp_name"));
            string tp_name = Marshal.PtrToStringAnsi(CPyMarshal.ReadPtr(tp_namePtr));
            
            string __name__ = tp_name;
            string __module__ = "";
            int lastDot = tp_name.LastIndexOf('.');
            if (lastDot != -1)
            {
                __name__ = tp_name.Substring(lastDot + 1);  
                __module__ = tp_name.Substring(0, lastDot);
            }
            classCode.Append(String.Format(CLASS_CODE, name, __module__));
            
            IntPtr tp_methodsPtr = CPyMarshal.Offset(
                typePtr, Marshal.OffsetOf(typeof(PyTypeObject), "tp_methods"));
            IntPtr methods = CPyMarshal.ReadPtr(tp_methodsPtr);
            if (methods != IntPtr.Zero)
            {
                this.GenerateMethods(
                    classCode, 
                    methods, 
                    (DispatchTable)module.Globals["_jumpy_dispatch_table"],
                    name + ".", 
                    NOARGS_METHOD_CODE, 
                    OBJARG_METHOD_CODE,
                    VARARGS_METHOD_CODE, 
                    VARARGS_KWARGS_METHOD_CODE
                );
            }
            classCode.Append(String.Format(CLASS_FIXUP_CODE, name, __name__));
            
            this.engine.Execute(classCode.ToString(), module);
            object klass = module.Globals[name];
            
            DynamicType.SetAttrMethod(klass, "_typePtr", typePtr);
            
            IntPtr tp_newOffset = Marshal.OffsetOf(typeof(PyTypeObject), "tp_new");
            IntPtr tp_newFP = CPyMarshal.ReadPtr(CPyMarshal.Offset(typePtr, tp_newOffset));
            PyType_GenericNew_Delegate tp_newDgt = (PyType_GenericNew_Delegate)
                Marshal.GetDelegateForFunctionPointer(
                    tp_newFP, typeof(PyType_GenericNew_Delegate));
            DynamicType.SetAttrMethod(klass, "_tp_newDgt", tp_newDgt);
            
            IntPtr tp_initOffset = Marshal.OffsetOf(typeof(PyTypeObject), "tp_init");
            IntPtr tp_initFP = CPyMarshal.ReadPtr(CPyMarshal.Offset(typePtr, tp_initOffset));
            CPython_initproc_Delegate tp_initDgt = (CPython_initproc_Delegate)
                Marshal.GetDelegateForFunctionPointer(
                    tp_initFP, typeof(CPython_initproc_Delegate));
            DynamicType.SetAttrMethod(klass, "_tp_initDgt", tp_initDgt);
            
            this.ptrmap[typePtr] = klass;
        }
        
        
        public override int 
        PyModule_AddObject(IntPtr modulePtr, string name, IntPtr itemPtr)
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
                    this.GenerateClass(module, name, itemPtr);
                }
            }
            return 0;
        }
        
        
        public override IntPtr 
        PyType_GenericNew(IntPtr typePtr, IntPtr args, IntPtr kwargs)
        {
            IntPtr tp_allocPtr = CPyMarshal.Offset(
                typePtr, Marshal.OffsetOf(typeof(PyTypeObject), "tp_alloc"));
            
            PyType_GenericAlloc_Delegate dgt = (PyType_GenericAlloc_Delegate)
                Marshal.GetDelegateForFunctionPointer(
                    CPyMarshal.ReadPtr(tp_allocPtr), typeof(PyType_GenericAlloc_Delegate));
            
            return dgt(typePtr, 0);
        }
        
        
        public override IntPtr 
        PyType_GenericAlloc(IntPtr typePtr, int nItems)
        {
            IntPtr tp_basicsizePtr = CPyMarshal.Offset(
                typePtr, Marshal.OffsetOf(typeof(PyTypeObject), "tp_basicsize"));
            int size = CPyMarshal.ReadInt(tp_basicsizePtr);
            
            if (nItems > 0)
            {
                IntPtr tp_itemsizePtr = CPyMarshal.Offset(
                    typePtr, Marshal.OffsetOf(typeof(PyTypeObject), "tp_itemsize"));
                int itemsize = CPyMarshal.ReadInt(tp_itemsizePtr);
                size += (nItems * itemsize);
            }
            
            IntPtr newInstance = this.allocator.Alloc(size);
            IntPtr iRefcountPtr = CPyMarshal.Offset(
                newInstance, Marshal.OffsetOf(typeof(PyObject), "ob_refcnt"));
            CPyMarshal.WriteInt(iRefcountPtr, 1);
            IntPtr iTypePtr = CPyMarshal.Offset(
                newInstance, Marshal.OffsetOf(typeof(PyObject), "ob_type"));
            CPyMarshal.WritePtr(iTypePtr, typePtr);
            return newInstance;
        }
    }
}