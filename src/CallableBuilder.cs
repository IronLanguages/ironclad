using System;
using System.Text;
using System.Runtime.InteropServices;

using IronPython.Runtime;

using Ironclad.Structs;

namespace Ironclad
{
    internal static class CallableBuilder
    {
        public static void
        GenerateFunctions(StringBuilder code, IntPtr methods, PythonDictionary methodTable)
        {
            GenerateCallablesFromMethodDefs(
                code, methods, methodTable, "",
                CodeSnippets.NOARGS_FUNCTION_CODE,
                CodeSnippets.OBJARG_FUNCTION_CODE,
                CodeSnippets.VARARGS_FUNCTION_CODE,
                CodeSnippets.VARARGS_KWARGS_FUNCTION_CODE);
        }

        public static void
        ExtractNameModule(string tp_name, ref string __name__, ref string __module__)
        {
            if (String.IsNullOrEmpty(tp_name))
            {
                __name__ = "unknown_type";
                __module__ = "";
                return;
            }

            string name = tp_name;
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

        public static void
        GenerateMethods(StringBuilder code, IntPtr methods, PythonDictionary methodTable, string tablePrefix)
        {
            GenerateCallablesFromMethodDefs(
                code, methods, methodTable, tablePrefix,
                CodeSnippets.NOARGS_METHOD_CODE,
                CodeSnippets.OBJARG_METHOD_CODE,
                CodeSnippets.VARARGS_METHOD_CODE,
                CodeSnippets.VARARGS_KWARGS_METHOD_CODE);
        }

        public static void
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
    }
}