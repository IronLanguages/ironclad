using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

using IronPython.Runtime;
using IronPython.Runtime.Calls;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Runtime;

using Ironclad.Structs;


namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {


        private void
        GenerateClass(IntPtr typePtr)
        {
            StringBuilder classCode = new StringBuilder();

            string __name__ = null;
            string __module__ = null;
            string tp_name = CPyMarshal.ReadCStringField(typePtr, typeof(PyTypeObject), "tp_name");
            this.ExtractNameModule(tp_name, ref __name__, ref __module__);

            string __doc__ = CPyMarshal.ReadCStringField(typePtr, typeof(PyTypeObject), "tp_doc").Replace("\\", "\\\\");
            classCode.Append(String.Format(CLASS_CODE, __name__, __module__, __doc__));

            string tablePrefix = __name__ + ".";
            PythonDictionary methodTable = new PythonDictionary();

            IntPtr ob_typePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "ob_type");
            object ob_type = this.Retrieve(ob_typePtr);
            this.UpdateMethodTable(methodTable, ob_type);
            this.IncRef(ob_typePtr);

            IntPtr tp_basePtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_base");
            if (tp_basePtr == IntPtr.Zero)
            {
                tp_basePtr = this.PyBaseObject_Type;
            }
            object tp_base = this.Retrieve(tp_basePtr);
            this.UpdateMethodTable(methodTable, tp_base);
            this.PyType_Ready(tp_basePtr);
            this.IncRef(tp_basePtr);

            PythonTuple tp_bases = null;
            IntPtr tp_basesPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_bases");
            if (tp_basesPtr != IntPtr.Zero)
            {
                tp_bases = (PythonTuple)this.Retrieve(tp_basesPtr);
                foreach (object _base in tp_bases)
                {
                    this.UpdateMethodTable(methodTable, _base);
                    IntPtr _basePtr = this.Store(_base);
                    this.PyType_Ready(_basePtr);
                }
                classCode.Append(CLASS_BASES_CODE);
            }

            this.ConnectTypeField(typePtr, tablePrefix, "tp_new", methodTable, typeof(PyType_GenericNew_Delegate));
            this.ConnectTypeField(typePtr, tablePrefix, "tp_init", methodTable, typeof(CPython_initproc_Delegate));

            IntPtr getsetPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_getset");
            this.GenerateProperties(classCode, getsetPtr, methodTable, tablePrefix);

            IntPtr membersPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_members");
            this.GenerateMembers(classCode, membersPtr, methodTable, tablePrefix);

            IntPtr methodsPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_methods");
            this.GenerateMethods(classCode, methodsPtr, methodTable, tablePrefix);

            IntPtr nmPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_as_number");
            this.GenerateNumberMethods(classCode, nmPtr, methodTable, tablePrefix);

            IntPtr sqPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_as_sequence");
            this.GenerateSequenceMethods(classCode, sqPtr, methodTable, tablePrefix);

            this.GenerateCallMethod(classCode, typePtr, methodTable, tablePrefix);
            this.GenerateIterMethods(classCode, typePtr, methodTable, tablePrefix);

            ScriptScope moduleScope = this.GetModuleScriptScope(this.scratchModule);
            moduleScope.SetVariable("_ironclad_baseclass", tp_base);
            moduleScope.SetVariable("_ironclad_metaclass", ob_type);
            moduleScope.SetVariable("_ironclad_bases", tp_bases);
            this.ExecInModule(classCode.ToString(), this.scratchModule);

            object klass = moduleScope.GetVariable<object>(__name__);
            Builtin.setattr(DefaultContext.Default, klass, "_typePtr", typePtr);
            object _dispatcher = PythonCalls.Call(this.dispatcherClass, new object[] { this, methodTable });
            Builtin.setattr(DefaultContext.Default, klass, "_dispatcher", _dispatcher);

            object typeDict = Builtin.getattr(DefaultContext.Default, klass, "__dict__");
            CPyMarshal.WritePtrField(typePtr, typeof(PyTypeObject), "tp_dict", this.Store(typeDict));

            this.map.Associate(typePtr, klass);
            this.IncRef(typePtr);
        }


        private void
        UpdateMethodTable(PythonDictionary methodTable, object _base)
        {
            if (Builtin.hasattr(DefaultContext.Default, _base, "_dispatcher"))
            {
                PythonDictionary baseMethodTable = (PythonDictionary)Builtin.getattr(
                    DefaultContext.Default, Builtin.getattr(
                        DefaultContext.Default, _base, "_dispatcher"), "table");
                methodTable.update(DefaultContext.Default, baseMethodTable);
            }
        }


        private void
        ConnectTypeField(IntPtr typePtr, string tablePrefix, string fieldName, PythonDictionary methodTable, Type dgtType)
        {
            if (CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), fieldName) != IntPtr.Zero)
            {
                Delegate dgt = CPyMarshal.ReadFunctionPtrField(
                    typePtr, typeof(PyTypeObject), fieldName, dgtType);
                methodTable[tablePrefix + fieldName] = dgt;
            }
        }


        private void
        GenerateCallablesFromMethodDefs(StringBuilder code,
                        IntPtr methods,
                        PythonDictionary methodTable,
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
                string name = thisMethod.ml_name;
                string template = null;
                Delegate dgt = null;

                bool unsupportedFlags = false;
                switch (thisMethod.ml_flags)
                {
                    case METH.NOARGS:
                        template = noargsTemplate;
                        dgt = Marshal.GetDelegateForFunctionPointer(
                            thisMethod.ml_meth,
                            typeof(CPythonVarargsFunction_Delegate));
                        break;

                    case METH.O:
                        template = objargTemplate;
                        dgt = Marshal.GetDelegateForFunctionPointer(
                            thisMethod.ml_meth,
                            typeof(CPythonVarargsFunction_Delegate));
                        break;

                    case METH.VARARGS:
                        template = varargsTemplate;
                        dgt = Marshal.GetDelegateForFunctionPointer(
                            thisMethod.ml_meth,
                            typeof(CPythonVarargsFunction_Delegate));
                        break;

                    case METH.VARARGS | METH.KEYWORDS:
                        template = varargsKwargsTemplate;
                        dgt = Marshal.GetDelegateForFunctionPointer(
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
                        name, thisMethod.ml_doc, tablePrefix));
                    methodTable[tablePrefix + name] = dgt;
                }
                else
                {
                    Console.WriteLine("Detected unsupported method flags for {0}{1}; ignoring.",
                        tablePrefix, name);
                }

                methodPtr = CPyMarshal.Offset(methodPtr, Marshal.SizeOf(typeof(PyMethodDef)));
            }
        }

        private void
        GenerateFunctions(StringBuilder code, IntPtr methods, PythonDictionary methodTable)
        {
            this.GenerateCallablesFromMethodDefs(
                code, methods, methodTable, "",
                NOARGS_FUNCTION_CODE,
                OBJARG_FUNCTION_CODE,
                VARARGS_FUNCTION_CODE,
                VARARGS_KWARGS_FUNCTION_CODE);
        }

        private void
        GenerateMethods(StringBuilder code, IntPtr methods, PythonDictionary methodTable, string tablePrefix)
        {
            this.GenerateCallablesFromMethodDefs(
                code, methods, methodTable, tablePrefix,
                NOARGS_METHOD_CODE,
                OBJARG_METHOD_CODE,
                VARARGS_METHOD_CODE,
                VARARGS_KWARGS_METHOD_CODE);
        }

        private void
        GenerateProperties(StringBuilder code, IntPtr getsets, PythonDictionary methodTable, string tablePrefix)
        {
            IntPtr getsetPtr = getsets;
            if (getsetPtr == IntPtr.Zero)
            {
                return;
            }
            while (CPyMarshal.ReadInt(getsetPtr) != 0)
            {
                PyGetSetDef thisGetset = (PyGetSetDef)Marshal.PtrToStructure(
                    getsetPtr, typeof(PyGetSetDef));
                string name = thisGetset.name;
                string doc = thisGetset.doc;
                IntPtr closure = thisGetset.closure;

                string getname = "None";
                if (thisGetset.get != IntPtr.Zero)
                {
                    getname = String.Format("__get_{0}", name);
                    CPython_getter_Delegate dgt = (CPython_getter_Delegate)
                        Marshal.GetDelegateForFunctionPointer(
                            thisGetset.get, typeof(CPython_getter_Delegate));
                    code.Append(String.Format(GETTER_METHOD_CODE, getname, tablePrefix, closure));
                    methodTable[tablePrefix + getname] = dgt;
                }

                string setname = "None";
                if (thisGetset.set != IntPtr.Zero)
                {
                    setname = String.Format("__set_{0}", name);
                    CPython_setter_Delegate dgt = (CPython_setter_Delegate)
                        Marshal.GetDelegateForFunctionPointer(
                            thisGetset.set, typeof(CPython_setter_Delegate));
                    code.Append(String.Format(SETTER_METHOD_CODE, setname, tablePrefix, closure));
                    methodTable[tablePrefix + setname] = dgt;
                }

                code.Append(String.Format(PROPERTY_CODE, name, getname, setname, doc));
                getsetPtr = CPyMarshal.Offset(getsetPtr, Marshal.SizeOf(typeof(PyGetSetDef)));
            }
        }


        private bool
        GetMemberMethodSuffix(MemberT type, ref string suffix)
        {
            switch (type)
            {
                case MemberT.INT:
                    suffix = "int";
                    return true;
                case MemberT.CHAR:
                    suffix = "char";
                    return true;
                case MemberT.UBYTE:
                    suffix = "ubyte";
                    return true;
                case MemberT.OBJECT:
                    suffix = "object";
                    return true;
                default:
                    return false;
            }
        }

        private void
        GenerateMembers(StringBuilder code, IntPtr members, PythonDictionary methodTable, string tablePrefix)
        {
            IntPtr memberPtr = members;
            if (memberPtr == IntPtr.Zero)
            {
                return;
            }

            while (CPyMarshal.ReadInt(memberPtr) != 0)
            {
                PyMemberDef thisMember = (PyMemberDef)Marshal.PtrToStructure(
                    memberPtr, typeof(PyMemberDef));
                string name = thisMember.name;
                int offset = thisMember.offset;
                string doc = thisMember.doc;

                string suffix = null;
                if (this.GetMemberMethodSuffix(thisMember.type, ref suffix))
                {
                    string getname = String.Format("__get_{0}", name);
                    code.Append(String.Format(MEMBER_GETTER_CODE, getname, offset, suffix));

                    string setname = "None";
                    if ((thisMember.flags & 1) == 0)
                    {
                        setname = String.Format("__set_{0}", name);
                        code.Append(String.Format(MEMBER_SETTER_CODE, setname, offset, suffix));
                    }
                    code.Append(String.Format(PROPERTY_CODE, name, getname, setname, doc));
                }
                else
                {
                    Console.WriteLine("detected unsupported member type {0}; ignoring", thisMember.type);
                }
                memberPtr = CPyMarshal.Offset(memberPtr, Marshal.SizeOf(typeof(PyMemberDef)));
            }
        }

        private void
        GenerateIterMethods(StringBuilder classCode, IntPtr typePtr, PythonDictionary methodTable, string tablePrefix)
        {
            Py_TPFLAGS tp_flags = (Py_TPFLAGS)CPyMarshal.ReadIntField(typePtr, typeof(PyTypeObject), "tp_flags");
            if ((tp_flags & Py_TPFLAGS.HAVE_ITER) == 0)
            {
                return;
            }
            if (CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_iter") != IntPtr.Zero)
            {
                classCode.Append(String.Format(ITER_METHOD_CODE, tablePrefix));
            }
            if (CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_iternext") != IntPtr.Zero)
            {
                classCode.Append(String.Format(ITERNEXT_METHOD_CODE, tablePrefix));
            }
            this.ConnectTypeField(typePtr, tablePrefix, "tp_iter", methodTable, typeof(CPythonSelfFunction_Delegate));
            this.ConnectTypeField(typePtr, tablePrefix, "tp_iternext", methodTable, typeof(CPythonSelfFunction_Delegate));
        }

        private void
        GenerateCallMethod(StringBuilder classCode, IntPtr typePtr, PythonDictionary methodTable, string tablePrefix)
        {
            IntPtr methodPtr = CPyMarshal.ReadPtrField(typePtr, typeof(PyTypeObject), "tp_call");
            if (methodPtr != IntPtr.Zero)
            {
                string name = "__call__";
                classCode.Append(String.Format(VARARGS_KWARGS_METHOD_CODE, name, "", tablePrefix));

                Delegate dgt = Marshal.GetDelegateForFunctionPointer(
                    methodPtr,
                    typeof(CPythonVarargsKwargsFunction_Delegate));
                methodTable[tablePrefix + name] = dgt;
            }
        }

        private void 
        GetMagicMethodInfo(string field, out string name, out string template, out Type dgtType)
        {
            switch (field)
            {
                case "nb_add": 
                    name = "__add__";
                    template = OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_subtract":
                    name = "__sub__";
                    template = OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "sq_item":
                    name = "__getitem__";
                    template = SSIZEARG_METHOD_CODE;
                    dgtType = typeof(CPython_ssizeargfunc_Delegate);
                    break;
                default:
                    throw new NotImplementedException(String.Format("unrecognised field: {0}", field));
            }
        }

        private void
        GenerateProtocolMagicMethods(StringBuilder classCode, IntPtr protocolPtr, Type protocol, string[] fields, PythonDictionary methodTable, string tablePrefix)
        {
            if (protocolPtr == IntPtr.Zero)
            {
                return;
            }
            foreach (string field in fields)
            {
                if (CPyMarshal.ReadPtrField(protocolPtr, protocol, field) != IntPtr.Zero)
                {
                    string name;
                    string template;
                    Type dgtType;
                    this.GetMagicMethodInfo(field, out name, out template, out dgtType);
                    methodTable[tablePrefix + name] = CPyMarshal.ReadFunctionPtrField(protocolPtr, protocol, field, dgtType); ;
                    classCode.Append(String.Format(template, name, "", tablePrefix));
                }
            }
        }

        private void
        GenerateSequenceMethods(StringBuilder classCode, IntPtr sqPtr, PythonDictionary methodTable, string tablePrefix)
        {
            string[] fields = new string[] { "sq_item" };
            this.GenerateProtocolMagicMethods(
                classCode, sqPtr, typeof(PySequenceMethods), fields, methodTable, tablePrefix);
        }

        private void
        GenerateNumberMethods(StringBuilder classCode, IntPtr nmPtr, PythonDictionary methodTable, string tablePrefix)
        {
            string[] fields = new string[] { "nb_add", "nb_subtract" };
            this.GenerateProtocolMagicMethods(
                classCode, nmPtr, typeof(PyNumberMethods), fields, methodTable, tablePrefix);
        }

        private void
        ExtractNameModule(string tp_name, ref string __name__, ref string __module__)
        {
            string name = tp_name;
            if (tp_name == "")
            {
                __name__ = "unnamed_type";
                __module__ = "";
                return;
            }

            string module = "";
            int lastDot = tp_name.LastIndexOf('.');
            if (lastDot != -1)
            {
                name = tp_name.Substring(lastDot + 1);
                module = tp_name.Substring(0, lastDot);
            }
            __name__ = name;
            __module__ = module;
        }
    }
}