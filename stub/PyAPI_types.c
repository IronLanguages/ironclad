
#define PyAPI_DATA(x) x
#define PyAPI_FUNC(x) x

#define Py_DEPRECATED(x)
typedef ssize_t Py_ssize_t;
#define PY_SSIZE_T_MAX ((Py_ssize_t)(((size_t)-1)>>1))
#define PY_SIZE_MAX ((size_t)-1)

#ifndef PY_FORMAT_SIZE_T
#   if SIZEOF_SIZE_T == SIZEOF_INT && !defined(__APPLE__)
#       define PY_FORMAT_SIZE_T ""
#   elif SIZEOF_SIZE_T == SIZEOF_LONG
#       define PY_FORMAT_SIZE_T "l"
#   elif defined(MS_WINDOWS)
#       define PY_FORMAT_SIZE_T "I"
#   else
#       error "This platform's pyconfig.h needs to define PY_FORMAT_SIZE_T"
#   endif
#endif

#define SIZEOF_LONG 4
#define SIZEOF_VOID_P 4

#define HAVE_LONG_LONG 1
#define PY_LONG_LONG long long

#define Py_GCC_ATTRIBUTE(x) __attribute__(x)
#define Py_SAFE_DOWNCAST(VALUE, WIDE, NARROW) (NARROW)(VALUE)

#define HAVE_SNPRINTF 1

/* Rich comparison opcodes */
#define Py_LT 0
#define Py_LE 1
#define Py_EQ 2
#define Py_NE 3
#define Py_GT 4
#define Py_GE 5


#define UCHAR_MAX 255
#define INT_MAX 2147483647
#define INT_MIN (-2147483647-1)
#define LONG_MAX 2147483647L
#define ULONG_MAX 4294967295UL
#define LONG_MIN (-2147483647L-1L)
#define SCHAR_MAX 127
#define SCHAR_MIN (-128)
#define SHRT_MAX 32767
#define SHRT_MIN (-32768)

#ifdef __CHAR_UNSIGNED__
#define Py_CHARMASK(c)		(c)
#else
#define Py_CHARMASK(c)		((c) & 0xff)
#endif

#define Py_TPFLAGS_HAVE_GETCHARBUFFER  (1L<<0)

#define HAVE_STDARG_PROTOTYPES 1


#define PyMem_MALLOC(n)         malloc((n) ? (n) : 1)
#define PyMem_REALLOC(p, n)     realloc((p), (n) ? (n) : 1)
#define PyMem_FREE		free
#define PyMem_New(type, n) \
  ( assert((n) <= PY_SIZE_MAX / sizeof(type)) , \
	( (type *) PyMem_Malloc((n) * sizeof(type)) ) )
#define PyMem_NEW(type, n) \
  ( assert((n) <= PY_SIZE_MAX / sizeof(type)) , \
	( (type *) PyMem_MALLOC((n) * sizeof(type)) ) )

#define PyMem_Resize(p, type, n) \
  ( assert((n) <= PY_SIZE_MAX / sizeof(type)) , \
	( (p) = (type *) PyMem_Realloc((p), (n) * sizeof(type)) ) )
#define PyMem_RESIZE(p, type, n) \
  ( assert((n) <= PY_SIZE_MAX / sizeof(type)) , \
	( (p) = (type *) PyMem_REALLOC((p), (n) * sizeof(type)) ) )

#define Py_MEMCPY memcpy


typedef struct _object {
	Py_ssize_t ob_refcnt;
	struct _typeobject *ob_type;
} PyObject;

#define Py_INCREF(op) (				\
	((op)->ob_refcnt)++)

#define Py_DECREF(op)					\
	if (--(op)->ob_refcnt == 0)	\
		(*(op)->ob_type->tp_dealloc)((PyObject *)(op))

#define Py_XINCREF(op) if ((op) == NULL) ; else Py_INCREF(op)
#define Py_XDECREF(op) if ((op) == NULL) ; else Py_DECREF(op)

typedef struct {
	Py_ssize_t ob_refcnt;
	struct _typeobject *ob_type;
	Py_ssize_t ob_size;
} PyVarObject;

typedef struct {
	Py_ssize_t ob_refcnt;
	struct _typeobject *ob_type;
    long ob_ival;
} PyIntObject;
#define PyInt_AS_LONG(op) (((PyIntObject *)(op))->ob_ival)

typedef struct {
	Py_ssize_t ob_refcnt;
	struct _typeobject *ob_type;
    double ob_fval;
} PyFloatObject;

typedef unsigned short digit;
struct _longobject {
	Py_ssize_t ob_refcnt;
	struct _typeobject *ob_type;
	Py_ssize_t ob_size;
	digit ob_digit[1];
};
typedef struct _longobject PyLongObject;

typedef struct {
    double real;
    double imag;
} Py_complex;

typedef struct {
	Py_ssize_t ob_refcnt;
	struct _typeobject *ob_type;
	Py_ssize_t ob_size;
    PyObject **ob_item;
    Py_ssize_t allocated;
} PyListObject;
#define PyList_GET_ITEM(op, i) (((PyListObject *)(op))->ob_item[i])
#define PyList_SET_ITEM(op, i, v) (((PyListObject *)(op))->ob_item[i] = (v))
#define PyList_GET_SIZE(op)    (((PyListObject *)(op))->ob_size)

#define PyList_Check(op) PyObject_TypeCheck(op, &PyList_Type)

typedef struct {
	Py_ssize_t ob_refcnt;
	struct _typeobject *ob_type;
	Py_ssize_t ob_size;
    PyObject *ob_item[1];
} PyTupleObject;
#define PyTuple_GET_ITEM(op, i) (((PyTupleObject *)(op))->ob_item[i])
#define PyTuple_SET_ITEM(op, i, v) (((PyTupleObject *)(op))->ob_item[i] = v)
#define PyTuple_GET_SIZE(op)    (((PyTupleObject *)(op))->ob_size)

typedef struct {
	Py_ssize_t ob_refcnt;
	struct _typeobject *ob_type;
	Py_ssize_t ob_size;
    long ob_shash;
    int ob_sstate;
    char ob_sval[1];
} PyStringObject;
#define PyString_AS_STRING(op) (((PyStringObject *)(op))->ob_sval)
#define PyString_GET_SIZE(op)  (((PyStringObject *)(op))->ob_size)

typedef wchar_t Py_UNICODE;
typedef struct {
	Py_ssize_t ob_refcnt;
	struct _typeobject *ob_type;
    Py_ssize_t length;
    Py_UNICODE *str;
    long hash;
    PyObject *defenc;
} PyUnicodeObject;


typedef PyObject * (*unaryfunc)(PyObject *);
typedef PyObject * (*binaryfunc)(PyObject *, PyObject *);
typedef PyObject * (*ternaryfunc)(PyObject *, PyObject *, PyObject *);
typedef int (*inquiry)(PyObject *);
typedef Py_ssize_t (*lenfunc)(PyObject *);
typedef int (*coercion)(PyObject **, PyObject **);
typedef PyObject *(*intargfunc)(PyObject *, int) Py_DEPRECATED(2.5);
typedef PyObject *(*intintargfunc)(PyObject *, int, int) Py_DEPRECATED(2.5);
typedef PyObject *(*ssizeargfunc)(PyObject *, Py_ssize_t);
typedef PyObject *(*ssizessizeargfunc)(PyObject *, Py_ssize_t, Py_ssize_t);
typedef int(*intobjargproc)(PyObject *, int, PyObject *);
typedef int(*intintobjargproc)(PyObject *, int, int, PyObject *);
typedef int(*ssizeobjargproc)(PyObject *, Py_ssize_t, PyObject *);
typedef int(*ssizessizeobjargproc)(PyObject *, Py_ssize_t, Py_ssize_t, PyObject *);
typedef int(*objobjargproc)(PyObject *, PyObject *, PyObject *);
typedef int (*getreadbufferproc)(PyObject *, int, void **);
typedef int (*getwritebufferproc)(PyObject *, int, void **);
typedef int (*getsegcountproc)(PyObject *, int *);
typedef int (*getcharbufferproc)(PyObject *, int, char **);
typedef Py_ssize_t (*readbufferproc)(PyObject *, Py_ssize_t, void **);
typedef Py_ssize_t (*writebufferproc)(PyObject *, Py_ssize_t, void **);
typedef Py_ssize_t (*segcountproc)(PyObject *, Py_ssize_t *);
typedef Py_ssize_t (*charbufferproc)(PyObject *, Py_ssize_t, char **);

typedef int (*objobjproc)(PyObject *, PyObject *);
typedef int (*visitproc)(PyObject *, void *);
typedef int (*traverseproc)(PyObject *, visitproc, void *);

typedef struct {
	binaryfunc nb_add;
	binaryfunc nb_subtract;
	binaryfunc nb_multiply;
	binaryfunc nb_divide;
	binaryfunc nb_remainder;
	binaryfunc nb_divmod;
	ternaryfunc nb_power;
	unaryfunc nb_negative;
	unaryfunc nb_positive;
	unaryfunc nb_absolute;
	inquiry nb_nonzero;
	unaryfunc nb_invert;
	binaryfunc nb_lshift;
	binaryfunc nb_rshift;
	binaryfunc nb_and;
	binaryfunc nb_xor;
	binaryfunc nb_or;
	coercion nb_coerce;
	unaryfunc nb_int;
	unaryfunc nb_long;
	unaryfunc nb_float;
	unaryfunc nb_oct;
	unaryfunc nb_hex;
	binaryfunc nb_inplace_add;
	binaryfunc nb_inplace_subtract;
	binaryfunc nb_inplace_multiply;
	binaryfunc nb_inplace_divide;
	binaryfunc nb_inplace_remainder;
	ternaryfunc nb_inplace_power;
	binaryfunc nb_inplace_lshift;
	binaryfunc nb_inplace_rshift;
	binaryfunc nb_inplace_and;
	binaryfunc nb_inplace_xor;
	binaryfunc nb_inplace_or;
	binaryfunc nb_floor_divide;
	binaryfunc nb_true_divide;
	binaryfunc nb_inplace_floor_divide;
	binaryfunc nb_inplace_true_divide;
	unaryfunc nb_index;
} PyNumberMethods;

typedef struct {
	lenfunc sq_length;
	binaryfunc sq_concat;
	ssizeargfunc sq_repeat;
	ssizeargfunc sq_item;
	ssizessizeargfunc sq_slice;
	ssizeobjargproc sq_ass_item;
	ssizessizeobjargproc sq_ass_slice;
	objobjproc sq_contains;
	binaryfunc sq_inplace_concat;
	ssizeargfunc sq_inplace_repeat;
} PySequenceMethods;

typedef struct {
	lenfunc mp_length;
	binaryfunc mp_subscript;
	objobjargproc mp_ass_subscript;
} PyMappingMethods;

typedef struct {
	readbufferproc bf_getreadbuffer;
	writebufferproc bf_getwritebuffer;
	segcountproc bf_getsegcount;
	charbufferproc bf_getcharbuffer;
} PyBufferProcs;


typedef void (*freefunc)(void *);
typedef void (*destructor)(PyObject *);
typedef int (*printfunc)(PyObject *, FILE *, int);
typedef PyObject *(*getattrfunc)(PyObject *, char *);
typedef PyObject *(*getattrofunc)(PyObject *, PyObject *);
typedef int (*setattrfunc)(PyObject *, char *, PyObject *);
typedef int (*setattrofunc)(PyObject *, PyObject *, PyObject *);
typedef int (*cmpfunc)(PyObject *, PyObject *);
typedef PyObject *(*reprfunc)(PyObject *);
typedef long (*hashfunc)(PyObject *);
typedef PyObject *(*richcmpfunc) (PyObject *, PyObject *, int);
typedef PyObject *(*getiterfunc) (PyObject *);
typedef PyObject *(*iternextfunc) (PyObject *);
typedef PyObject *(*descrgetfunc) (PyObject *, PyObject *, PyObject *);
typedef int (*descrsetfunc) (PyObject *, PyObject *, PyObject *);
typedef int (*initproc)(PyObject *, PyObject *, PyObject *);
typedef PyObject *(*newfunc)(struct _typeobject *, PyObject *, PyObject *);
typedef PyObject *(*allocfunc)(struct _typeobject *, Py_ssize_t);

typedef struct _typeobject {
	Py_ssize_t ob_refcnt;
	struct _typeobject *ob_type;
	Py_ssize_t ob_size;
	const char *tp_name; /* For printing, in format "<module>.<name>" */
	Py_ssize_t tp_basicsize, tp_itemsize; /* For allocation */
	destructor tp_dealloc;
	printfunc tp_print;
	getattrfunc tp_getattr;
	setattrfunc tp_setattr;
	cmpfunc tp_compare;
	reprfunc tp_repr;
	PyNumberMethods *tp_as_number;
	PySequenceMethods *tp_as_sequence;
	PyMappingMethods *tp_as_mapping;
	hashfunc tp_hash;
	ternaryfunc tp_call;
	reprfunc tp_str;
	getattrofunc tp_getattro;
	setattrofunc tp_setattro;
	PyBufferProcs *tp_as_buffer;
	long tp_flags;
	const char *tp_doc; /* Documentation string */
	traverseproc tp_traverse;
	inquiry tp_clear;
	richcmpfunc tp_richcompare;
	Py_ssize_t tp_weaklistoffset;
	getiterfunc tp_iter;
	iternextfunc tp_iternext;
	struct PyMethodDef *tp_methods;
	struct PyMemberDef *tp_members;
	struct PyGetSetDef *tp_getset;
	struct _typeobject *tp_base;
	PyObject *tp_dict;
	descrgetfunc tp_descr_get;
	descrsetfunc tp_descr_set;
	Py_ssize_t tp_dictoffset;
	initproc tp_init;
	allocfunc tp_alloc;
	newfunc tp_new;
	freefunc tp_free; /* Low-level free-memory routine */
	inquiry tp_is_gc; /* For PyObject_IS_GC */
	PyObject *tp_bases;
	PyObject *tp_mro; /* method resolution order */
	PyObject *tp_cache;
	PyObject *tp_subclasses;
	PyObject *tp_weaklist;
	destructor tp_del;
} PyTypeObject;

typedef struct {
	Py_ssize_t ob_refcnt;
	struct _typeobject *ob_type;
    PyObject	*cl_bases;	/* A tuple of class objects */
    PyObject	*cl_dict;	/* A dictionary */
    PyObject	*cl_name;	/* A string */
    /* The following three are functions or NULL */
    PyObject	*cl_getattr;
    PyObject	*cl_setattr;
    PyObject	*cl_delattr;
} PyClassObject;

typedef struct {
	Py_ssize_t ob_refcnt;
	struct _typeobject *ob_type;
    PyClassObject *in_class;	/* The class object */
    PyObject	  *in_dict;	/* A dictionary */
    PyObject	  *in_weakreflist; /* List of weak references */
} PyInstanceObject;

#define PyType_HasFeature(t,f)  (((t)->tp_flags & (f)) != 0)

#define PyObject_TypeCheck(ob, tp) \
	((ob)->ob_type == (tp) || PyType_IsSubtype((ob)->ob_type, (tp)))

#define PyType_Check(op) PyObject_TypeCheck(op, &PyType_Type)


#define PyClass_Check(op) ((op)->ob_type == &PyClass_Type)
#define PyInstance_Check(op) ((op)->ob_type == &PyInstance_Type)
#define PyTuple_Check(op) PyObject_TypeCheck(op, &PyTuple_Type)
#define PyString_Check(op) PyObject_TypeCheck(op, &PyString_Type)
#define PyFloat_Check(op) PyObject_TypeCheck(op, &PyFloat_Type)
#define PyInt_Check(op) PyObject_TypeCheck(op, &PyInt_Type)
#define PyLong_Check(op) PyObject_TypeCheck(op, &PyLong_Type)
#define PyDict_Check(op) PyObject_TypeCheck(op, &PyDict_Type)
#define PyDict_CheckExact(op) ((op)->ob_type == &PyDict_Type)
#define PyCObject_Check(op) ((op)->ob_type == &PyCObject_Type)
#define PyBuffer_Check(op) ((op)->ob_type == &PyBuffer_Type)
#define PyTraceBack_Check(v) ((v)->ob_type == &PyTraceBack_Type)
#define Py_END_OF_BUFFER	(-1)


#define PyObject_MALLOC		PyObject_Malloc
#define PyObject_FREE		PyObject_Free
#define PyObject_DEL		PyObject_FREE

#define _PyObject_SIZE(typeobj) ( (typeobj)->tp_basicsize )

#define PyObject_NEW(type, typeobj) \
( (type *) PyObject_Init( \
	(PyObject *) PyObject_MALLOC( _PyObject_SIZE(typeobj) ), (typeobj)) )


#define PyDoc_VAR(name) static char name[]
#define PyDoc_STRVAR(name,str) PyDoc_VAR(name) = PyDoc_STR(str)
#define PyDoc_STR(str) str


typedef
    enum {PyGILState_LOCKED, PyGILState_UNLOCKED}
        PyGILState_STATE;

typedef void (*PyOS_sighandler_t)(int);

//typedef int (*Py_tracefunc)(PyObject *, struct _frame *, int, PyObject *);
typedef int (*Py_tracefunc)(PyObject *, void *, int, PyObject *);

typedef void PyInterpreterState;

#define PyThreadState_GET() (_PyThreadState_Current)

typedef struct _ts {
    /* See Python/ceval.c for comments explaining most fields */

    struct _ts *next;
    PyInterpreterState *interp;

    struct _frame *frame;
    int recursion_depth;
    /* 'tracing' keeps track of the execution depth when tracing/profiling.
       This is to prevent the actual trace/profile code from being recorded in
       the trace/profile. */
    int tracing;
    int use_tracing;

    Py_tracefunc c_profilefunc;
    Py_tracefunc c_tracefunc;
    PyObject *c_profileobj;
    PyObject *c_traceobj;

    PyObject *curexc_type;
    PyObject *curexc_value;
    PyObject *curexc_traceback;

    PyObject *exc_type;
    PyObject *exc_value;
    PyObject *exc_traceback;

    PyObject *dict;  /* Stores per-thread state */

    /* tick_counter is incremented whenever the check_interval ticker
     * reaches zero. The purpose is to give a useful measure of the number
     * of interpreted bytecode instructions in a given thread.  This
     * extremely lightweight statistic collector may be of interest to
     * profilers (like psyco.jit()), although nothing in the core uses it.
     */
    int tick_counter;

    int gilstate_counter;

    PyObject *async_exc; /* Asynchronous exception to raise */
    long thread_id; /* Thread id where this tstate was created */

    /* XXX signal handlers should also be here */

} PyThreadState;

// Faked declarations for things we hope never to use, ever:

typedef void PyCompilerFlags;
typedef void PyArena;
typedef void PyCodeObject;
typedef void PyFrameObject;
typedef void PyAddrPair;
typedef void PyFutureFeatures;
typedef void PyTryBlock;
typedef void PyGenObject;
//typedef void PyMethodChain;
typedef void PySliceObject;
typedef void PyStructSequence_Desc;
typedef void PySTEntryObject;
typedef void PyWeakReference;

typedef void *PyThread_type_lock;
typedef void *PyThread_type_sema;

typedef void *mod_ty;
typedef void node;
typedef void grammar;
typedef void perrdetail;

// typedef struct _frame *(*PyThreadFrameGetter)(PyThreadState *self_);
typedef void *(*PyThreadFrameGetter)(PyThreadState *self_);


// These functions differ from the Python implementation - They use the 'faucet model of cycle detection'.
#define PyObject_GC_New(type, typeobj) \
		( (type *) _PyObject_New(typeobj) )
#define _PyObject_GC_TRACK(op)
#define _PyObject_GC_UNTRACK
// end difference


#define _PyObject_HEAD_EXTRA
#define PyObject_HEAD			\
	_PyObject_HEAD_EXTRA		\
	Py_ssize_t ob_refcnt;		\
	struct _typeobject *ob_type;

#define _PyObject_EXTRA_INIT
#define PyObject_HEAD_INIT(type)	\
	_PyObject_EXTRA_INIT		\
	1, type,


#define T_OBJECT	6
#define WRITE_RESTRICTED 4


typedef struct PyMemberDef {
	/* Current version, use this */
	char *name;
	int type;
	Py_ssize_t offset;
	int flags;
	char *doc;
} PyMemberDef;

#define offsetof(type, member) ( (int) & ((type*)0) -> member )


/* Utility macro to help write tp_traverse functions.
 * To use this macro, the tp_traverse function must name its arguments
 * "visit" and "arg".  This is intended to keep tp_traverse functions
 * looking as much alike as possible.
 */
#define Py_VISIT(op)							\
        do { 								\
                if (op) {						\
                        int vret = visit((PyObject *)(op), arg);	\
                        if (vret)					\
                                return vret;				\
                }							\
        } while (0)
