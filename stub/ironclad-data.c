 
// NOTE: anything defined herein should be filled in by the mapper;
// leaving them uninitialised may lead to surprising runtime behaviour

// various types

PyTypeObject PyType_Type;
PyTypeObject PyBaseObject_Type;
PyTypeObject PyClass_Type;
PyTypeObject PyInstance_Type;
PyTypeObject PyMethod_Type;
PyTypeObject PyCode_Type;
PyTypeObject PyComplex_Type;
PyTypeObject PyWrapperDescr_Type;
PyTypeObject PyProperty_Type;
PyTypeObject PyDict_Type;
PyTypeObject PyEnum_Type;
PyTypeObject PyReversed_Type;
PyTypeObject PyFile_Type;
PyTypeObject PyFloat_Type;
PyTypeObject PyFrame_Type;
PyTypeObject PyFunction_Type;
PyTypeObject PyClassMethod_Type;
PyTypeObject PyStaticMethod_Type;
PyTypeObject PyGen_Type;
PyTypeObject PyInt_Type;
PyTypeObject PyBool_Type;
PyTypeObject PySeqIter_Type;
PyTypeObject PyCallIter_Type;
PyTypeObject PyList_Type;
PyTypeObject PyLong_Type;
PyTypeObject PyCFunction_Type;
PyTypeObject PyModule_Type;
PyTypeObject PySuper_Type;
PyTypeObject PyRange_Type;
PyTypeObject PySet_Type;
PyTypeObject PyFrozenSet_Type;
PyTypeObject PySlice_Type;
PyTypeObject PyBaseString_Type;
PyTypeObject PySTEntry_Type;
PyTypeObject PyString_Type;
PyTypeObject PySymtableEntry_Type;
PyTypeObject PyTraceBack_Type;
PyTypeObject PyTuple_Type;
PyTypeObject PyUnicode_Type;
PyTypeObject PyNone_Type;
PyTypeObject PyEllipsis_Type;
PyTypeObject PyNotImplemented_Type;
PyTypeObject _PyWeakref_RefType;
PyTypeObject _PyWeakref_ProxyType;
PyTypeObject _PyWeakref_CallableProxyType;
PyTypeObject PyNullImporter_Type;
PyTypeObject PyByteArray_Type;
PyTypeObject PyByteArrayIter_Type;


// Parser/graminit.c
void* _PyParser_Grammar[100];


// Parser/myreadline.c
char *(*PyOS_ReadlineFunctionPointer)(FILE *, FILE *, char *) = NULL;
PyThreadState* _PyOS_ReadlineTState;

// Objects/object.c
PyObject _Py_NoneStruct;
PyObject _Py_NotImplementedStruct;
int _PyTrash_delete_nesting = 0;
PyObject *_PyTrash_delete_later = NULL;

// Objects/boolobject.c
PyIntObject _Py_ZeroStruct;
PyIntObject _Py_TrueStruct;


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

const char *Py_FileSystemDefaultEncoding = NULL;

// PC/config.c -- this is not filled in; we're hoping nothing uses it for anything important
// I don't think the SWIG usage matters, because we automatically call initfoo functions
// from elsewhere
struct _inittab _PyImport_Inittab[1000];
// Python/import.c
struct _inittab *PyImport_Inittab = _PyImport_Inittab;

// replacements for stuff defined in Objects/exceptions.c
PyObject * PyExc_BaseException;
PyObject * PyExc_Exception;
PyObject * PyExc_StopIteration;
PyObject * PyExc_GeneratorExit;
PyObject * PyExc_StandardError;
PyObject * PyExc_ArithmeticError;
PyObject * PyExc_LookupError;
PyObject * PyExc_AssertionError;
PyObject * PyExc_AttributeError;
PyObject * PyExc_EOFError;
PyObject * PyExc_FloatingPointError;
PyObject * PyExc_EnvironmentError;
PyObject * PyExc_IOError;
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
#ifdef MS_WINDOWS
PyObject * PyExc_WindowsError;
#endif
#ifdef __VMS
PyObject * PyExc_VMSError;
#endif
PyObject * PyExc_BufferError;
PyObject * PyExc_MemoryErrorInst;
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
