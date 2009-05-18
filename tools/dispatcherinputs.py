
from tools.dispatchersnippets import *

# args for generate_dispatcher_field
dispatcher_field_types = (
    (('int', 'int', 'Int'), {}),
    (('uint', 'uint', 'UInt'), {}),
    (('double', 'double', 'Double'), {}),
    (('ubyte', 'byte', 'Byte'), {}),
    (('char', 'string', 'Byte'), {'gettweak': 'Builtin.chr', 'settweak': '(byte)Builtin.ord'}),
)

# args for generate_dispatcher_method
dispatcher_PyCFunc_convenience_methods = (
    (('ic_function_noargs', 'obj_objobj'), {'argtweak': ('module', 'null')}),
    (('ic_method_noargs', 'obj_objobj'), {'argtweak': (0, 'null')}),
    (('ic_function_objarg', 'obj_objobj'), {'argtweak': ('module', 0)}),
    (('ic_method_objarg', 'obj_objobj'), {}),
    (('ic_function_varargs', 'obj_objobj'), {'argtweak': ('module', 0)}),
    (('ic_method_varargs', 'obj_objobj'), {}),
    (('ic_function_kwargs', 'obj_objobjobj'), {'argtweak': ('module', 0, 1), 'nullablekwargs': 1}),
    (('ic_method_kwargs', 'obj_objobjobj'), {'nullablekwargs': 2}),
    
    (('ic_method_getter', 'obj_objptr'), {}),
    (('ic_method_setter', 'int_objobjptr'), {'rettweak': THROW_RET_NEGATIVE}),
)

# args for generate_dispatcher_method
# not all of these are necessarily used yet
dispatcher_header_functypes = (
    # object.h
    (('unaryfunc', 'obj_obj'), {}),
    (('binaryfunc', 'obj_objobj'), {}),
    (('ternaryfunc', 'obj_objobjobj'), {}),
    (('inquiry', 'int_obj'), {}),
    (('lenfunc', 'size_obj'), {}),
    (('coercion', 'int_ptrptr'), {}),
    (('intargfunc', 'obj_objint'), {}),
    (('intintargfunc', 'obj_objintint'), {}),
    (('ssizeargfunc', 'obj_objsize'), {}),
    (('ssizessizeargfunc', 'obj_objsizesize'), {}),
    (('intobjargproc', 'int_objintobj'), {}),
    (('intintobjargproc', 'int_objintintobj'), {}),
    (('ssizeobjargproc', 'int_objsizeobj'), {'rettweak': THROW_RET_NEGATIVE}),
    (('ssizessizeobjargproc', 'int_objsizesizeobj'), {'rettweak': THROW_RET_NEGATIVE}),
    (('objobjargproc', 'int_objobjobj'), {'rettweak': THROW_RET_NEGATIVE}),

    (('getreadbufferproc', 'int_objintptr'), {}),
    (('getwritebufferproc', 'int_objintptr'), {}),
    (('getsegcountproc', 'int_objptr'), {}),
    (('getcharbufferproc', 'int_objintptr'), {}),
    (('readbufferproc', 'size_objsizeptr'), {}),
    (('writebufferproc', 'size_objsizeptr'), {}),
    (('segcountproc', 'size_objptr'), {}),
    (('charbufferproc', 'size_objsizeptr'), {}),
    
    (('objobjproc', 'int_objobj'), {}),
    (('visitproc', 'int_objptr'), {}),
    (('traverseproc', 'int_objptrptr'), {}),
    
    (('freefunc', 'void_ptr'), {}),
    (('destructor', 'void_obj'), {'rettweak': HANDLE_RET_DESTRUCTOR}),
    (('printfunc', 'int_objptrint'), {}),
    (('getattrfunc', 'obj_objstr'), {}),
    (('getattrofunc', 'obj_objobj'), {}),
    (('setattrfunc', 'int_objstrobj'), {}),
    (('setattrofunc', 'int_objobjobj'), {}),
    (('cmpfunc', 'int_objobj'), {}),
    (('reprfunc', 'obj_obj'), {}),
    (('hashfunc', 'long_obj'), {}),
    (('richcmpfunc', 'obj_objobjint'), {}),
    (('getiterfunc', 'obj_obj'), {}),
    (('iternextfunc', 'obj_obj'), {'rettweak': ITERNEXT_HANDLE_RETPTR}),
    (('descrgetfunc', 'obj_objobjobj'), {}),
    (('descrsetfunc', 'int_objobjobj'), {}),
    (('initproc', 'int_objobjobj'), {'rettweak': THROW_RET_NEGATIVE, 'nullablekwargs': 2}),
    (('newfunc', 'obj_objobjobj'), {'nullablekwargs': 2}),
    (('allocfunc', 'obj_objsize'), {}),
    
    # desrcobject.h
    (('getter', 'obj_objptr'), {}),
    (('setter', 'int_objobjptr'), {}),
    
    # cobject.c (note: destructor already defined above; 
    # destructor2 only ever used internally, while destroying PyCObjects)
    (('destructor2', 'void_objptr'), {}),
    
    # apparently not worth giving this one a formal identifier
    # but you're expected to pass them to Py_AtExit
    (('unnamed', 'void_void'), {}),
)

dispatcher_methods = dispatcher_PyCFunc_convenience_methods + dispatcher_header_functypes

# args for generate_magic_method
protocol_field_types = (
    # note that missing fields, unless noted, just aren't handled yet
    
    # PyTypeObject
    # new and del should always be set up anyway
    # richcmp is tricky and needs special handling
    (('tp_init', 'initproc', '__init__'), {'template': SQUISHKWARGS_TEMPLATE_TEMPLATE}),
    (('tp_iter', 'getiterfunc', '__iter__'), {}),
    (('tp_iternext', 'iternextfunc', 'next'), {}),
    (('tp_str', 'reprfunc', '__str__'), {}),
    (('tp_repr', 'reprfunc', '__repr__'), {}),
    (('tp_call', 'ternaryfunc', '__call__'), {'template': SQUISHKWARGS_TEMPLATE_TEMPLATE}),
    (('tp_hash', 'hashfunc', '__hash__'), {}),
    (('tp_compare', 'cmpfunc', '__cmp__'), {}),
    (('tp_getattr', 'getattrfunc', '__getattr__'), {}), # tweaks needed eventually? (getattro)
    
    # PyNumberMethods
    (('nb_add', 'binaryfunc', '__add__'), {'swapped': '__radd__'}),
    (('nb_subtract', 'binaryfunc', '__sub__'), {'swapped': '__rsub__'}),
    (('nb_multiply', 'binaryfunc', '__mul__'), {'swapped': '__rmul__'}),
    (('nb_divide', 'binaryfunc', '__div__'), {'swapped': '__rdiv__'}),
    (('nb_remainder', 'binaryfunc', '__mod__'), {'swapped': '__rmod__'}),
    (('nb_divmod', 'binaryfunc', '__divmod__'), {'swapped': '__rdivmod__'}),
    (('nb_power', 'ternaryfunc', '__pow__'), {'swapped': '__rpow__', 'template': POW_TEMPLATE_TEMPLATE, 'swappedtemplate': POW_SWAPPED_TEMPLATE_TEMPLATE}),
    (('nb_negative', 'unaryfunc', '__neg__'), {}),
    (('nb_positive', 'unaryfunc', '__pos__'), {}),
    (('nb_absolute', 'unaryfunc', '__abs__'), {}),
    (('nb_nonzero', 'inquiry', '__nonzero__'), {}),
    (('nb_invert', 'unaryfunc', '__invert__'), {}),
    (('nb_lshift', 'binaryfunc', '__lshift__'), {'swapped': '__rlshift__'}),
    (('nb_rshift', 'binaryfunc', '__rshift__'), {'swapped': '__rrshift__'}),
    (('nb_and', 'binaryfunc', '__and__'), {'swapped': '__rand__'}),
    (('nb_xor', 'binaryfunc', '__xor__'), {'swapped': '__rxor__'}),
    (('nb_or', 'binaryfunc', '__or__'), {'swapped': '__ror__'}),
    (('nb_int', 'unaryfunc', '__int__'), {}),
    (('nb_long', 'unaryfunc', '__long__'), {}),
    (('nb_float', 'unaryfunc', '__float__'), {}),
    (('nb_oct', 'unaryfunc', '__oct__'), {}),
    (('nb_hex', 'unaryfunc', '__hex__'), {}),
    (('nb_inplace_add', 'binaryfunc', '__iadd__'), {}),
    (('nb_inplace_subtract', 'binaryfunc', '__isub__'), {}),
    (('nb_inplace_multiply', 'binaryfunc', '__imul__'), {}),
    (('nb_inplace_divide', 'binaryfunc', '__idiv__'), {}),
    (('nb_inplace_remainder', 'binaryfunc', '__imod__'), {}),
    (('nb_inplace_power', 'ternaryfunc', '__ipow__'), {'template': POW_TEMPLATE_TEMPLATE}),
    (('nb_inplace_lshift', 'binaryfunc', '__ilshift__'), {}),
    (('nb_inplace_rshift', 'binaryfunc', '__irshift__'), {}),
    (('nb_inplace_and', 'binaryfunc', '__iand__'), {}),
    (('nb_inplace_xor', 'binaryfunc', '__ixor__'), {}),
    (('nb_inplace_or', 'binaryfunc', '__ior__'), {}),
    (('nb_true_divide', 'binaryfunc', '__truediv__'), {'swapped': '__rtruediv__'}),
    (('nb_floor_divide', 'binaryfunc', '__floordiv__'), {'swapped': '__rfloordiv__'}),
    (('nb_inplace_true_divide', 'binaryfunc', '__itruediv__'), {}),
    (('nb_inplace_floor_divide', 'binaryfunc', '__ifloordiv__'), {}),
    (('nb_index', 'unaryfunc', '__index__'), {}),

    # PySequenceMethods
    (('sq_length', 'lenfunc', '__len__'), {'template': LEN_TEMPLATE_TEMPLATE}),
    (('sq_concat', 'binaryfunc', '__add__'), {}),
    (('sq_item', 'ssizeargfunc', '__getitem__'), {}),
    (('sq_slice', 'ssizessizeargfunc', '__getslice__'), {'template': SQ_SLICE_HACK_TEMPLATE_TEMPLATE}),
    (('sq_ass_item', 'ssizeobjargproc', '__setitem__'), {}),
    (('sq_ass_slice', 'ssizessizeobjargproc', '__setslice__'), {'template': SQ_SLICE_HACK_TEMPLATE_TEMPLATE}),
    (('sq_contains', 'objobjproc', '__contains__'), {}),
    
    # PyMappingMethods
    (('mp_length', 'lenfunc', '__len__'), {'template': LEN_TEMPLATE_TEMPLATE}),
    (('mp_subscript', 'binaryfunc', '__getitem__'), {}),
    (('mp_ass_subscript', 'objobjargproc', '__setitem__'), {}),
)

# these really should be autogenerated, although
# some of them will be a little tricky.
known_python25api_signatures = (
    ('_PyLong_Sign', 'int_ptr'),
    ('_PyObject_New', 'ptr_ptr'),
    ('_PyString_Resize', 'int_ptrsize'),
    ('_PyTuple_Resize', 'int_ptrsize'),
    
    ('Py_AtExit', 'int_ptr'),
    ('Py_InitModule4', 'ptr_strptrstrptrint'),
    
    ('PyBool_FromLong', 'ptr_long'),
    
    ('PyCallable_Check', 'int_ptr'),
    
    ('PyClass_New', 'ptr_ptrptrptr'),
    
    ('PyCode_New', 'ptr_intintintintptrptrptrptrptrptrptrptrintptr'),
    
    ('PyComplex_AsCComplex', 'cpx_ptr'),
    ('PyComplex_FromDoubles', 'ptr_doubledouble'),
    
    ('PyDict_DelItem', 'int_ptrptr'),
    ('PyDict_DelItemString', 'int_ptrstr'),
    ('PyDict_GetItem', 'ptr_ptrptr'),
    ('PyDict_GetItemString', 'ptr_ptrstr'),
    ('PyDict_New', 'ptr_void'),
    ('PyDict_Next', 'int_ptrptrptrptr'),
    ('PyDict_SetItem', 'int_ptrptrptr'),
    ('PyDict_SetItemString', 'int_ptrstrptr'),
    ('PyDict_Size', 'size_ptr'),
    ('PyDict_Update', 'int_ptrptr'),
    ('PyDict_Values', 'ptr_ptr'),
    
    ('PyDictProxy_New', 'ptr_ptr'),
    
    ('PyErr_GivenExceptionMatches', 'int_ptrptr'),
    ('PyErr_NewException', 'ptr_strptrptr'),
    ('PyErr_Print', 'void_void'),
    
    ('PyEval_GetBuiltins', 'ptr_void'),
    ('PyEval_InitThreads', 'void_void'),
    ('PyEval_RestoreThread', 'void_ptr'),
    ('PyEval_SaveThread', 'ptr_void'),
    
    ('PyFloat_AsDouble', 'double_ptr'),
    ('PyFloat_FromDouble', 'ptr_double'),
    
    ('PyFrame_New', 'ptr_ptrptrptrptr'),
    
    ('PyGILState_Ensure', 'int_void'), # warning, not really int
    ('PyGILState_Release', 'void_int'), # warning, not really int
    
    ('PyImport_AddModule', 'ptr_str'),
    ('PyImport_GetModuleDict', 'ptr_void'),
    ('PyImport_Import', 'ptr_ptr'),
    ('PyImport_ImportModule', 'ptr_str'),
    
    ('PyInt_AsLong', 'long_ptr'),
    ('PyInt_AsSsize_t', 'size_ptr'),
    ('PyInt_AsUnsignedLongMask', 'ulong_ptr'),
    ('PyInt_FromLong', 'ptr_long'),
    ('PyInt_FromSsize_t', 'ptr_size'),
    
    ('PyIter_Next', 'ptr_ptr'),
    
    ('PyList_Append', 'int_ptrptr'),
    ('PyList_GetItem', 'ptr_ptrsize'),
    ('PyList_GetSlice', 'ptr_ptrsizesize'),
    ('PyList_New', 'ptr_size'),
    ('PyList_SetItem', 'int_ptrsizeptr'),
    
    ('PyLong_AsLong', 'long_ptr'),
    ('PyLong_AsLongLong', 'llong_ptr'),
    ('PyLong_AsUnsignedLong', 'ulong_ptr'),
    ('PyLong_AsUnsignedLongLong', 'ullong_ptr'),
    ('PyLong_FromDouble', 'ptr_double'),
    ('PyLong_FromLong', 'ptr_long'),
    ('PyLong_FromLongLong', 'ptr_llong'),
    ('PyLong_FromUnsignedLong', 'ptr_ulong'),
    ('PyLong_FromUnsignedLongLong', 'ptr_ullong'),
    
    ('PyMapping_Check', 'int_ptr'),
    ('PyMapping_GetItemString', 'ptr_ptrstr'),
    
    ('PyMem_Free', 'void_ptr'),
    ('PyMem_Malloc', 'ptr_size'),
    ('PyMem_Realloc', 'ptr_ptrsize'),
    
    ('PyMethod_New', 'ptr_ptrptrptr'),
    
    ('PyModule_AddIntConstant', 'int_ptrstrlong'),
    ('PyModule_AddObject', 'int_ptrstrptr'),
    ('PyModule_AddStringConstant', 'int_ptrstrstr'),
    ('PyModule_GetDict', 'ptr_ptr'),
    ('PyModule_New', 'ptr_str'),
    
    ('PyNumber_Absolute', 'ptr_ptr'),
    ('PyNumber_Add', 'ptr_ptrptr'),
    ('PyNumber_And', 'ptr_ptrptr'),
    ('PyNumber_Check', 'int_ptr'),
    ('PyNumber_Divide', 'ptr_ptrptr'),
    ('PyNumber_Float', 'ptr_ptr'),
    ('PyNumber_FloorDivide', 'ptr_ptrptr'),
    ('PyNumber_Index', 'ptr_ptr'),
    ('PyNumber_InPlaceRemainder', 'ptr_ptrptr'),
    ('PyNumber_Int', 'ptr_ptr'),
    ('PyNumber_Long', 'ptr_ptr'),
    ('PyNumber_Lshift', 'ptr_ptrptr'),
    ('PyNumber_Multiply', 'ptr_ptrptr'),
    ('PyNumber_Or', 'ptr_ptrptr'),
    ('PyNumber_Remainder', 'ptr_ptrptr'),
    ('PyNumber_Rshift', 'ptr_ptrptr'),
    ('PyNumber_Subtract', 'ptr_ptrptr'),
    ('PyNumber_TrueDivide', 'ptr_ptrptr'),
    ('PyNumber_Xor', 'ptr_ptrptr'),
    
    ('PyObject_Call', 'ptr_ptrptrptr'),
    ('PyObject_Compare', 'int_ptrptr'),
    ('PyObject_DelItemString', 'int_ptrstr'),
    ('PyObject_Free', 'void_ptr'),
    ('PyObject_GetAttr', 'ptr_ptrptr'),
    ('PyObject_GetAttrString', 'ptr_ptrstr'),
    ('PyObject_GetItem', 'ptr_ptrptr'),
    ('PyObject_GetIter', 'ptr_ptr'),
    ('PyObject_HasAttr', 'int_ptrptr'),
    ('PyObject_HasAttrString', 'int_ptrstr'),
    ('PyObject_Hash', 'long_ptr'),
    ('PyObject_Init', 'ptr_ptrptr'),
    ('PyObject_IsInstance', 'int_ptrptr'),
    ('PyObject_IsSubclass', 'int_ptrptr'),
    ('PyObject_IsTrue', 'int_ptr'),
    ('PyObject_Malloc', 'ptr_size'),
    ('PyObject_Realloc', 'ptr_ptrsize'),
    ('PyObject_Repr', 'ptr_ptr'),
    ('PyObject_RichCompare', 'ptr_ptrptrint'),
    ('PyObject_RichCompareBool', 'int_ptrptrint'),
    ('PyObject_SelfIter', 'ptr_ptr'),
    ('PyObject_SetAttr', 'int_ptrptrptr'),
    ('PyObject_SetAttrString', 'int_ptrstrptr'),
    ('PyObject_SetItem', 'int_ptrptrptr'),
    ('PyObject_Size', 'size_ptr'),
    ('PyObject_Str', 'ptr_ptr'),
    
    ('PyRun_StringFlags', 'ptr_strintptrptrptr'),
    
    ('PySeqIter_New', 'ptr_ptr'),
    
    ('PySequence_Check', 'int_ptr'),
    ('PySequence_Concat', 'ptr_ptrptr'),
    ('PySequence_GetItem', 'ptr_ptrsize'),
    ('PySequence_GetSlice', 'ptr_ptrsizesize'),
    ('PySequence_Repeat', 'ptr_ptrsize'),
    ('PySequence_SetItem', 'int_ptrsizeptr'),
    ('PySequence_Size', 'size_ptr'),
    ('PySequence_Tuple', 'ptr_ptr'),
    
    ('PySlice_New', 'ptr_ptrptrptr'),
    
    # the use of ptrs instead of strs is entirely deliberate
    ('PyString_AsString', 'ptr_ptr'),
    ('PyString_AsStringAndSize', 'int_ptrptrptr'),
    ('PyString_Concat', 'void_ptrptr'),
    ('PyString_ConcatAndDel', 'void_ptrptr'),
    ('PyString_FromString', 'ptr_ptr'),
    ('PyString_FromStringAndSize', 'ptr_ptrsize'),
    ('PyString_InternFromString', 'ptr_ptr'),
    ('PyString_InternInPlace', 'void_ptr'),
    ('PyString_Repr', 'ptr_ptrint'),
    ('PyString_Size', 'size_ptr'),
    
    ('PySys_GetObject', 'ptr_str'),
    
    # not sure ptrs here are really ptrs
    ('PyThread_acquire_lock', 'int_ptrint'),
    ('PyThread_allocate_lock', 'ptr_void'),
    ('PyThread_free_lock', 'void_ptr'),
    ('PyThread_release_lock', 'void_ptr'),
    
    ('PyTraceBack_Here', 'void_ptr'),
    
    ('PyTuple_GetSlice', 'ptr_ptrsizesize'),
    ('PyTuple_New', 'ptr_size'),
    ('PyTuple_Size', 'size_ptr'),
    
    ('PyType_GenericAlloc', 'ptr_ptrsize'),
    ('PyType_GenericNew', 'ptr_ptrptrptr'),
    ('PyType_IsSubtype', 'int_ptrptr'),
    ('PyType_Ready', 'int_ptr'),
)

# C# methods which need to have function ptrs stored for one reason or another
extra_python25api_signatures = (
    ('IC_PyBaseObject_Dealloc', 'void_ptr'),
    ('IC_PyBaseObject_Init', 'int_ptrptrptr'),
    ('IC_PyDict_Init', 'int_ptrptrptr'),
    ('IC_PyFloat_New', 'ptr_ptrptrptr'),
    ('IC_PyInstance_Dealloc', 'void_ptr'),
    ('IC_PyInt_New', 'ptr_ptrptrptr'),
    ('IC_PyType_New', 'ptr_ptrptrptr'),
    ('IC_PyList_Dealloc', 'void_ptr'),
    ('IC_PySlice_Dealloc', 'void_ptr'),
    ('IC_PyTuple_Dealloc', 'void_ptr'),
    ('IC_PyString_Str', 'ptr_ptr'),
    ('IC_PyString_Concat_Core', 'ptr_ptrptr'),
    ('IC_str_getreadbuffer', 'size_ptrsizeptr'),
    ('IC_str_getwritebuffer', 'size_ptrsizeptr'),
    ('IC_str_getsegcount', 'size_ptrptr'),
    
    ('IC_PyFile_AsFile', 'ptr_ptr'),
    ('IC_file_dealloc', 'void_ptr'),
)

import os
_in_this_dir = lambda name: os.path.join(os.path.dirname(__file__), name)
all_functions_file = _in_this_dir("python25ApiFunctions")
c_functions_file = "stub/_ignore_symbols"
data_items_file = _in_this_dir("python25ApiDataItems")


wrangler_input_keys = set([
    'dispatcher_field_types', 
    'dispatcher_methods',
    'protocol_field_types',
    'known_python25api_signatures',
    'extra_python25api_signatures',
    'all_functions_file',
    'c_functions_file',
    'data_items_file',
])

WRANGLER_INPUT = dict((k, v) for (k, v) in locals().items() if k in wrangler_input_keys)
