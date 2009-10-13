
// filled in by Python25Api; just need to exist somewhere

PyTypeObject PyNotImplemented_Type;
PyTypeObject PyEllipsis_Type;
PyTypeObject PyNone_Type;

// perhaps possible to use real gc module

PyObject *
_PyObject_GC_Malloc(size_t basicsize)
{
    return PyObject_Malloc(basicsize);
}

PyObject *
_PyObject_GC_New(PyTypeObject *tp)
{
	return _PyObject_New(tp);
}

PyVarObject *
_PyObject_GC_NewVar(PyTypeObject *tp, Py_ssize_t nitems)
{
	return _PyObject_NewVar(tp, nitems);
}

void
PyObject_GC_Del(void *op)
{
	PyObject_Del(op);
}

void PyObject_GC_Track(void *_) {}
void PyObject_GC_UnTrack(void *_) {}


// traceback hacks for Pyrex; truly, truly evil

PyCodeObject *
PyCode_New(
	int _0, int _1, int _2, int _3, PyObject *_4, PyObject *_5, PyObject *_6, PyObject *_7,
	PyObject *_8, PyObject *_9, PyObject *_10, PyObject *funcname, int _12, PyObject *_13)
{
	Py_INCREF(funcname);
	return (PyCodeObject*)funcname;
}

PyFrameObject *
PyFrame_New(PyThreadState *_0, PyCodeObject *code, PyObject *_2, PyObject *_3)
{
	Py_INCREF(code);
	return (PyFrameObject*)code;
}

int
PyTraceBack_Here(struct _frame *frame)
{
	PyThreadState *tstate = PyThreadState_GET();
	PyTracebackObject *oldtb = (PyTracebackObject *) tstate->curexc_traceback;

	PyObject *tb = (PyObject*)frame;
	Py_INCREF(tb);

	if (tb == NULL)
		return -1;
	tstate->curexc_traceback = (PyObject *)tb;
	Py_XDECREF(oldtb);
	return 0;
}

// originaly defined in Python/pythonrun.c; entirely faked-up here

void Py_Initialize(void) {}
void Py_InitializeEx(int _) {}
void Py_Finalize(void) {}
int Py_IsInitialized(void) { return 1; }

// Python/ceval.c

int
PyEval_GetRestricted(void)
{
	return 0;
}

// Parser/graminit.c

void* _PyParser_Grammar[1000] = {0,};

// Objects/typeobject.c
void
PyType_Modified(PyTypeObject *type)
{
	// do nothing for now -- the only use I'm aware of is in h5py, which
	// sometimes modifed types' __dict__s, which ipy is capable of dealing
	// with itself.
}

// TODO: I don't understand why this works, but somehow it apparently does
int fstat(int fd, struct stat* buffer)
{
	return _fstat64i32(fd, (struct _stat64i32*)buffer);
}
