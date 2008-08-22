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
                case "nb_or":
                    name = "__or__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_and":
                    name = "__and__";
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
                case "nb_int":
                    name = "__int__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "nb_negative":
                    name = "__neg__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "nb_invert":
                    name = "__invert__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "nb_power":
                    name = "__pow__";
                    template = CodeSnippets.TERNARY_METHOD_CODE;
                    dgtType = typeof(CPython_ternaryfunc_Delegate);
                    break;
                case "nb_nonzero":
                    name = "__nonzero__";
                    template = CodeSnippets.INQURY_METHOD_CODE;
                    dgtType = typeof(CPython_inquiry_Delegate);
                    break;

                // PySequenceMethods
                case "sq_item":
                    name = "_getitem_sq_item";
                    template = CodeSnippets.SSIZEARG_METHOD_CODE;
                    dgtType = typeof(CPython_ssizeargfunc_Delegate);
                    break;
                case "sq_slice":
                    name = "__getslice__";
                    template = CodeSnippets.SSIZESSIZEARG_METHOD_CODE;
                    dgtType = typeof(CPython_ssizessizeargfunc_Delegate);
                    break;
                case "sq_length":
                    name = "__len__";
                    template = CodeSnippets.LENFUNC_METHOD_CODE;
                    dgtType = typeof(CPython_lenfunc_Delegate);
                    break;

                // PyMappingMethods
                case "mp_subscript":
                    name = "_getitem_mp_subscript";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                    
                // b0rked
                default:
                    throw new NotImplementedException(String.Format("unrecognised field: {0}", field));
            }
        }
    }
}