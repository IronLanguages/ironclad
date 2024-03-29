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
                CodeSnippets.NOARGS_FUNCTION_TEMPLATE,
                CodeSnippets.OBJARG_FUNCTION_TEMPLATE,
                CodeSnippets.VARARGS_FUNCTION_TEMPLATE,
                CodeSnippets.VARARGS_KWARGS_FUNCTION_TEMPLATE);
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
                CodeSnippets.NOARGS_METHOD_TEMPLATE,
                CodeSnippets.OBJARG_METHOD_TEMPLATE,
                CodeSnippets.VARARGS_METHOD_TEMPLATE,
                CodeSnippets.VARARGS_KWARGS_METHOD_TEMPLATE);
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

                // COEXIST flag ignored; which method is chosen depends on order of calls in ClassBuilder.
                bool unsupportedFlags = false;
                METH flags = (METH)thisMethod.ml_flags & ~(METH.COEXIST | METH.CLASS | METH.STATIC); // TODO: ignoring CLASS and STATIC is not correct...
                switch (flags)
                {
                    case METH.NOARGS:
                        template = noargsTemplate;
                        dgt = Marshal.GetDelegateForFunctionPointer(
                            thisMethod.ml_meth,
                            typeof(dgt_ptr_ptrptr));
                        break;

                    case METH.O:
                        template = objargTemplate;
                        dgt = Marshal.GetDelegateForFunctionPointer(
                            thisMethod.ml_meth,
                            typeof(dgt_ptr_ptrptr));
                        break;

                    case METH.VARARGS:
                        template = varargsTemplate;
                        dgt = Marshal.GetDelegateForFunctionPointer(
                            thisMethod.ml_meth,
                            typeof(dgt_ptr_ptrptr));
                        break;

                    case METH.KEYWORDS:
                    case METH.VARARGS | METH.KEYWORDS:
                        template = varargsKwargsTemplate;
                        dgt = Marshal.GetDelegateForFunctionPointer(
                            thisMethod.ml_meth,
                            typeof(dgt_ptr_ptrptrptr));
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
                    Console.WriteLine("Detected unsupported method flags for {0}{1} ({2}); ignoring.",
                        tablePrefix, name, thisMethod.ml_flags);
                }

                methodPtr = CPyMarshal.Offset(methodPtr, Marshal.SizeOf<PyMethodDef>());
            }
        }
    }
}
