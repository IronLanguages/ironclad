 
// NOTE: anything defined herein should be filled in by the mapper;
// leaving them uninitialised may lead to surprising runtime behaviour

// various types

PyTypeObject PyBaseObject_Type;
PyTypeObject PyBool_Type;
PyTypeObject PyByteArrayIter_Type;
PyTypeObject PyByteArray_Type;
PyTypeObject PyBytesIter_Type;
PyTypeObject PyBytes_Type;
PyTypeObject PyCFunction_Type;
PyTypeObject PyCallIter_Type;
PyTypeObject PyCapsule_Type;
PyTypeObject PyCell_Type;
PyTypeObject PyClassMethodDescr_Type;
PyTypeObject PyClassMethod_Type;
PyTypeObject PyCode_Type;
PyTypeObject PyComplex_Type;
PyTypeObject PyDictItems_Type;
PyTypeObject PyDictIterItem_Type;
PyTypeObject PyDictIterKey_Type;
PyTypeObject PyDictIterValue_Type;
PyTypeObject PyDictKeys_Type;
PyTypeObject PyDictProxy_Type;
PyTypeObject PyDictValues_Type;
PyTypeObject PyDict_Type;
PyTypeObject PyEllipsis_Type;
PyTypeObject PyEnum_Type;
PyTypeObject PyFilter_Type;
PyTypeObject PyFloat_Type;
PyTypeObject PyFrame_Type;
PyTypeObject PyFrozenSet_Type;
PyTypeObject PyFunction_Type;
PyTypeObject PyGen_Type;
PyTypeObject PyGetSetDescr_Type;
PyTypeObject PyInstanceMethod_Type;
PyTypeObject PyListIter_Type;
PyTypeObject PyListRevIter_Type;
PyTypeObject PyList_Type;
PyTypeObject PyLongRangeIter_Type;
PyTypeObject PyLong_Type;
PyTypeObject PyMap_Type;
PyTypeObject PyMemberDescr_Type;
PyTypeObject PyMemoryView_Type;
PyTypeObject PyMethodDescr_Type;
PyTypeObject PyMethod_Type;
PyTypeObject PyModule_Type;
PyTypeObject PyProperty_Type;
PyTypeObject PyRangeIter_Type;
PyTypeObject PyRange_Type;
PyTypeObject PyReversed_Type;
PyTypeObject PySTEntry_Type;
PyTypeObject PySeqIter_Type;
PyTypeObject PySetIter_Type;
PyTypeObject PySet_Type;
PyTypeObject PySlice_Type;
PyTypeObject PyStaticMethod_Type;
PyTypeObject PyStdPrinter_Type;
PyTypeObject PySuper_Type;
PyTypeObject PyTraceBack_Type;
PyTypeObject PyTupleIter_Type;
PyTypeObject PyTuple_Type;
PyTypeObject PyType_Type;
PyTypeObject PyUnicodeIter_Type;
PyTypeObject PyUnicode_Type;
PyTypeObject PyWrapperDescr_Type;
PyTypeObject PyZip_Type;
PyTypeObject _PyManagedBuffer_Type;
PyTypeObject _PyMethodWrapper_Type;
PyTypeObject _PyNamespace_Type;
PyTypeObject _PyNone_Type;
PyTypeObject _PyNotImplemented_Type;
PyTypeObject _PyWeakref_ProxyType;
PyTypeObject _PyWeakref_RefType;
PyTypeObject _PyWeakref_CallableProxyType;

// Parser/graminit.c
void* _PyParser_Grammar[100];


// Parser/myreadline.c
char *(*PyOS_ReadlineFunctionPointer)(FILE *, FILE *, const char *) = NULL;
PyThreadState* _PyOS_ReadlineTState;

// Objects/object.c
PyObject _Py_NoneStruct;
PyObject _Py_NotImplementedStruct;
int _PyTrash_delete_nesting = 0;
PyObject *_PyTrash_delete_later = NULL;
_Py_HashSecret_t _Py_HashSecret;

// Objects/boolobject.c
PyIntObject _Py_ZeroStruct;
PyIntObject _Py_TrueStruct;
PyIntObject _Py_FalseStruct;

// Objects/bytearray.h
char _PyByteArray_empty_string[2] = {0,0};

// Objects/sliceobject.c
PyObject _Py_EllipsisObject;


// Python/pystate.c
int (*PyOS_InputHook)(void) = NULL;
PyThreadState *_PyThreadState_Current;
PyThreadFrameGetter _PyThreadState_GetFrame = NULL;


// Python/modsupport.c
char *_Py_PackageContext = NULL;


// Python/ceval.c
int _Py_CheckInterval = 100;
int _Py_Ticker = 100;
#ifndef Py_DEFAULT_RECURSION_LIMIT
#define Py_DEFAULT_RECURSION_LIMIT 1000
#endif
int _Py_CheckRecursionLimit = Py_DEFAULT_RECURSION_LIMIT;


// Python/pythonrun.c
int Py_NoUserSiteDirectory = 0;
PyThreadState *_Py_Finalizing;


// Python/frozen.c
static struct _frozen _PyImport_FrozenModules[] = { {0, 0, 0} };
struct _frozen *PyImport_FrozenModules = _PyImport_FrozenModules;


// whole bunch of flags, mostly from pythonrun:
int Py_DebugFlag = 0;
int Py_DivisionWarningFlag = 0;
int Py_Py3kWarningFlag = 0;
int Py_IgnoreEnvironmentFlag = 0;
int Py_FrozenFlag = 0;
int Py_VerboseFlag = 0;
int Py_UnicodeFlag = 0;
int Py_BytesWarningFlag = 0;
int Py_TabcheckFlag = 0;
int _Py_QnewFlag = 0;
int Py_InteractiveFlag = 0;
int Py_NoSiteFlag = 0;
int Py_InspectFlag = 0;
int Py_OptimizeFlag = 2; // prevents numpy from crashing when trying to set docstrings
int Py_UseClassExceptionsFlag = 1;
int Py_DontWriteBytecodeFlag = 0;
int Py_HashRandomizationFlag = 0; /* for -R and PYTHONHASHSEED */

const char *Py_FileSystemDefaultEncoding = NULL;

// PC/config.c -- this is not filled in; we're hoping nothing uses it for anything important
// I don't think the SWIG usage matters, because we automatically call initfoo functions
// from elsewhere
struct _inittab _PyImport_Inittab[1000];
// Python/import.c
struct _inittab *PyImport_Inittab = _PyImport_Inittab;

// replacements for stuff defined in Objects/exceptions.c
// TODO: can we use definitions from pyerrors.h instead?
PyObject * PyExc_BaseException;
PyObject * PyExc_Exception;
PyObject * PyExc_StopIteration;
PyObject * PyExc_GeneratorExit;
PyObject * PyExc_ArithmeticError;
PyObject * PyExc_LookupError;
PyObject * PyExc_AssertionError;
PyObject * PyExc_AttributeError;
PyObject * PyExc_BufferError;
PyObject * PyExc_EOFError;
PyObject * PyExc_FloatingPointError;
PyObject * PyExc_OSError;
PyObject * PyExc_ImportError;
PyObject * PyExc_IndexError;
PyObject * PyExc_KeyError;
PyObject * PyExc_KeyboardInterrupt;
PyObject * PyExc_MemoryError;
PyObject * PyExc_NameError;
PyObject * PyExc_OverflowError;
PyObject * PyExc_RuntimeError;
PyObject * PyExc_NotImplementedError;
PyObject * PyExc_SyntaxError;
PyObject * PyExc_IndentationError;
PyObject * PyExc_TabError;
PyObject * PyExc_ReferenceError;
PyObject * PyExc_SystemError;
PyObject * PyExc_SystemExit;
PyObject * PyExc_TypeError;
PyObject * PyExc_UnboundLocalError;
PyObject * PyExc_UnicodeError;
PyObject * PyExc_UnicodeEncodeError;
PyObject * PyExc_UnicodeDecodeError;
PyObject * PyExc_UnicodeTranslateError;
PyObject * PyExc_ValueError;
PyObject * PyExc_ZeroDivisionError;
PyObject * PyExc_BlockingIOError;
PyObject * PyExc_BrokenPipeError;
PyObject * PyExc_ChildProcessError;
PyObject * PyExc_ConnectionError;
PyObject * PyExc_ConnectionAbortedError;
PyObject * PyExc_ConnectionRefusedError;
PyObject * PyExc_ConnectionResetError;
PyObject * PyExc_FileExistsError;
PyObject * PyExc_FileNotFoundError;
PyObject * PyExc_InterruptedError;
PyObject * PyExc_IsADirectoryError;
PyObject * PyExc_NotADirectoryError;
PyObject * PyExc_PermissionError;
PyObject * PyExc_ProcessLookupError;
PyObject * PyExc_TimeoutError;
PyObject * PyExc_EnvironmentError;
PyObject * PyExc_IOError;
#ifdef MS_WINDOWS
PyObject * PyExc_WindowsError;
#endif
PyObject * PyExc_RecursionErrorInst;
PyObject * PyExc_Warning;
PyObject * PyExc_UserWarning;
PyObject * PyExc_DeprecationWarning;
PyObject * PyExc_PendingDeprecationWarning;
PyObject * PyExc_SyntaxWarning;
PyObject * PyExc_RuntimeWarning;
PyObject * PyExc_FutureWarning;
PyObject * PyExc_ImportWarning;
PyObject * PyExc_UnicodeWarning;
PyObject * PyExc_BytesWarning;
PyObject * PyExc_ResourceWarning;

// TODO: get rid of these - not in 3.4

PyTypeObject PyNone_Type; // renamed to _PyNone_Type
PyTypeObject PyNotImplemented_Type; // renamed to _PyNotImplemented_Type
PyTypeObject PySymtableEntry_Type; // renamed to PySTEntry_Type
PyTypeObject PyClass_Type; // removed
PyTypeObject PyInt_Type; // removed
PyTypeObject PyInstance_Type; // removed
PyTypeObject PyBaseString_Type; // removed
PyObject * PyExc_MemoryErrorInst;

// TODO: sort these out

int Py_UnbufferedStdioFlag;
int Py_IsolatedFlag;
int Py_QuietFlag;
PyObject * _PySet_Dummy;
int Py_HasFileSystemDefaultEncoding;
int _PyOS_opterr;
int _PyOS_optind;
char * _PyOS_optarg;
const char * Py_hexdigits;
