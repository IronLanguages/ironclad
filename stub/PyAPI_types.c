
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

#define PyType_HasFeature(t,f)  (((t)->tp_flags & (f)) != 0)

#define PyObject_TypeCheck(ob, tp) \
	((ob)->ob_type == (tp) || PyType_IsSubtype((ob)->ob_type, (tp)))

#define PyTuple_Check(op) PyObject_TypeCheck(op, &PyTuple_Type)
#define PyString_Check(op) PyObject_TypeCheck(op, &PyString_Type)
#define PyFloat_Check(op) PyObject_TypeCheck(op, &PyFloat_Type)
#define PyInt_Check(op) PyObject_TypeCheck(op, &PyInt_Type)
#define PyLong_Check(op) PyObject_TypeCheck(op, &PyLong_Type)
#define PyDict_Check(op) PyObject_TypeCheck(op, &PyDict_Type)
#define PyDict_CheckExact(op) ((op)->ob_type == &PyDict_Type)


typedef PyObject *(*PyCFunction)(PyObject *, PyObject *);
typedef PyObject *(*PyCFunctionWithKeywords)(PyObject *, PyObject *,
					     PyObject *);
typedef PyObject *(*PyNoArgsFunction)(PyObject *);

struct PyMethodDef {
    const char	*ml_name;	/* The name of the built-in function/method */
    PyCFunction  ml_meth;	/* The C function that implements it */
    int		 ml_flags;	/* Combination of METH_xxx flags, which mostly
				   describe the args expected by the C func */
    const char	*ml_doc;	/* The __doc__ attribute, or NULL */
};
typedef struct PyMethodDef PyMethodDef;


typedef
    enum {PyGILState_LOCKED, PyGILState_UNLOCKED}
        PyGILState_STATE;

typedef void (*PyOS_sighandler_t)(int);



// Faked declarations for things we hope never to use, ever:

typedef void PyThreadState;
typedef void PyCompilerFlags;
typedef void PyArena;
typedef void PyCodeObject;
typedef void PyFrameObject;
typedef void PyAddrPair;
typedef void PyFutureFeatures;
typedef void PyTryBlock;
typedef void PyGenObject;
typedef void PyMethodChain;
typedef void PyInterpreterState;
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

//typedef int (*Py_tracefunc)(PyObject *, struct _frame *, int, PyObject *);
typedef int (*Py_tracefunc)(PyObject *, void *, int, PyObject *);

// typedef struct _frame *(*PyThreadFrameGetter)(PyThreadState *self_);
typedef void *(*PyThreadFrameGetter)(PyThreadState *self_);
