using System;

namespace Ironclad
{
    public class MagicMethods
    {
        public static void
        GetInfo(string field, out string name, out string template, out Type dgtType, out bool needGetSwappedInfo)
        {
            needGetSwappedInfo = false;
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
                    needGetSwappedInfo = true;
                    break;
                case "nb_subtract":
                    name = "__sub__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    needGetSwappedInfo = true;
                    break;
                case "nb_multiply":
                    name = "__mul__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    needGetSwappedInfo = true;
                    break;
                case "nb_divide":
                    name = "__div__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    needGetSwappedInfo = true;
                    break;
                case "nb_true_divide":
                    name = "__truediv__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    needGetSwappedInfo = true;
                    break;
                case "nb_floor_divide":
                    name = "__floordiv__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    needGetSwappedInfo = true;
                    break;
                case "nb_remainder":
                    name = "__mod__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    needGetSwappedInfo = true;
                    break;
                case "nb_divmod":
                    name = "__divmod__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    needGetSwappedInfo = true;
                    break;
                case "nb_lshift":
                    name = "__lshift__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    needGetSwappedInfo = true;
                    break;
                case "nb_rshift":
                    name = "__rshift__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    needGetSwappedInfo = true;
                    break;
                case "nb_and":
                    name = "__and__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    needGetSwappedInfo = true;
                    break;
                case "nb_xor":
                    name = "__xor__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    needGetSwappedInfo = true;
                    break;
                case "nb_or":
                    name = "__or__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    needGetSwappedInfo = true;
                    break;

                case "nb_inplace_add":
                    name = "__iadd__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_inplace_subtract":
                    name = "__isub__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_inplace_multiply":
                    name = "__imul__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_inplace_divide":
                    name = "__idiv__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_inplace_true_divide":
                    name = "__itruediv__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_inplace_floor_divide":
                    name = "__ifloordiv__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_inplace_remainder":
                    name = "__imod__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_inplace_lshift":
                    name = "__ilshift__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_inplace_rshift":
                    name = "__irshift__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_inplace_and":
                    name = "__iand__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_inplace_xor":
                    name = "__ixor__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_inplace_or":
                    name = "__ior__";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;

                case "nb_negative":
                    name = "__neg__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "nb_positive":
                    name = "__pos__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "nb_absolute":
                    name = "__abs__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "nb_invert":
                    name = "__invert__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "nb_int":
                    name = "__int__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "nb_long":
                    name = "__long__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "nb_float":
                    name = "__float__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "nb_oct":
                    name = "__oct__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "nb_hex":
                    name = "__hex__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                case "nb_index":
                    name = "__index__";
                    template = CodeSnippets.SELFARG_METHOD_CODE;
                    dgtType = typeof(CPython_unaryfunc_Delegate);
                    break;
                    
                case "nb_power":
                    name = "__pow__";
                    template = CodeSnippets.TERNARY_METHOD_CODE;
                    dgtType = typeof(CPython_ternaryfunc_Delegate);
                    needGetSwappedInfo = true;
                    break;
                case "nb_inplace_power":
                    name = "__ipow__";
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
                case "sq_ass_item":
                    name = "_setitem_sq_ass_item";
                    template = CodeSnippets.SSIZEOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_ssizeobjargproc_Delegate);
                    break;
                case "sq_slice":
                    name = "__getslice__";
                    template = CodeSnippets.SSIZESSIZEARG_METHOD_CODE;
                    dgtType = typeof(CPython_ssizessizeargfunc_Delegate);
                    break;
                case "sq_ass_slice":
                    name = "__setslice__";
                    template = CodeSnippets.SSIZESSIZEOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_ssizessizeobjargproc_Delegate);
                    break;
                case "sq_length":
                    name = "_len_sq_length";
                    template = CodeSnippets.LENFUNC_METHOD_CODE;
                    dgtType = typeof(CPython_lenfunc_Delegate);
                    break;

                // PyMappingMethods
                case "mp_subscript":
                    name = "_getitem_mp_subscript";
                    template = CodeSnippets.OBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "mp_ass_subscript":
                    name = "_setitem_mp_ass_subscript";
                    template = CodeSnippets.OBJOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_objobjargproc_Delegate);
                    break;
                case "mp_length":
                    name = "_len_mp_length";
                    template = CodeSnippets.LENFUNC_METHOD_CODE;
                    dgtType = typeof(CPython_lenfunc_Delegate);
                    break;
                    
                // b0rked
                default:
                    throw new NotImplementedException(String.Format("unrecognised field: {0}", field));
            }
        }
        
        public static void
        GetSwappedInfo(string field, out string name, out string template, out Type dgtType)
        {
            switch (field)
            {
                case "nb_add":
                    name = "__radd__";
                    template = CodeSnippets.SWAPPEDOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_subtract":
                    name = "__rsub__";
                    template = CodeSnippets.SWAPPEDOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_multiply":
                    name = "__rmul__";
                    template = CodeSnippets.SWAPPEDOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_divide":
                    name = "__rdiv__";
                    template = CodeSnippets.SWAPPEDOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_true_divide":
                    name = "__rtruediv__";
                    template = CodeSnippets.SWAPPEDOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_floor_divide":
                    name = "__rfloordiv__";
                    template = CodeSnippets.SWAPPEDOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_remainder":
                    name = "__rmod__";
                    template = CodeSnippets.SWAPPEDOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_divmod":
                    name = "__rdivmod__";
                    template = CodeSnippets.SWAPPEDOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_lshift":
                    name = "__rlshift__";
                    template = CodeSnippets.SWAPPEDOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_rshift":
                    name = "__rrshift__";
                    template = CodeSnippets.SWAPPEDOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_and":
                    name = "__rand__";
                    template = CodeSnippets.SWAPPEDOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_xor":
                    name = "__rxor__";
                    template = CodeSnippets.SWAPPEDOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_or":
                    name = "__ror__";
                    template = CodeSnippets.SWAPPEDOBJARG_METHOD_CODE;
                    dgtType = typeof(CPython_binaryfunc_Delegate);
                    break;
                case "nb_power":
                    name = "__rpow__";
                    template = CodeSnippets.SWAPPEDTERNARY_METHOD_CODE;
                    dgtType = typeof(CPython_ternaryfunc_Delegate);
                    break;
            
                default:
                    throw new NotImplementedException(String.Format("unrecognised field: {0}", field));
            }
        }
    }
}