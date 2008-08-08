using System;

namespace Ironclad
{
    public class MagicMethods
    {
        public static void
        GetInfo(string field, out string name, out string template, out Type dgtType)
        {
            switch (field)
            {
                // PyTypeObject
                case "tp_str":
                    name = "__str__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "tp_repr":
                    name = "__repr__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "tp_call":
                    name = "__call__";
                    template = CodeSnippets.VARARGS_KWARGS_METHOD_CODE;
                    dgtType = typeof(CPythonVarargsKwargsFunction_Delegate);
                    break;

                // PyNumberMethods
                case "nb_add":
                    name = "__add__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_subtract":
                    name = "__sub__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_multiply":
                    name = "__mul__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_divide":
                    name = "__div__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_absolute":
                    name = "__abs__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "nb_float":
                    name = "__float__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;

                // PySequenceMethods
                case "sq_item":
                    name = "__getitem__";
                    template = CodeSnippets.SSIZEARG_METHOD_CODE;
                    dgtType = typeof(CPython_ssizeargfunc_Delegate);
                    break;
                case "sq_length":
                    name = "__len__";
                    template = CodeSnippets.LENFUNC_METHOD_CODE;
                    dgtType = typeof(CPython_lenfunc_Delegate);
                    break;
                    
                // b0rked
                default:
                    throw new NotImplementedException(String.Format("unrecognised field: {0}", field));
            }
        }
    }
}