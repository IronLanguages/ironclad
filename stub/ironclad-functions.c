
// TODO: perhaps possible to use real gc module

PyObject *
_PyObject_GC_Malloc(size_t basicsize)
{
    return (PyObject*)PyObject_Malloc(basicsize);
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


// originally defined in Python/pythonrun.c; entirely faked-up here

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

// Objects/typeobject.c
void
PyType_Modified(PyTypeObject *type)
{
	// do nothing for now -- the only use I'm aware of is in h5py, which
	// sometimes modifed types' __dict__s, which ipy is capable of dealing
	// with itself.
}

PyObject**
_PyObject_GetDictPtr(PyObject *obj)
{
    return NULL;
}


// TODO: this will break, when you least expect it, because it assumes that
// _off_t and time_t are both 32-bit. OTOH, the users don't seem to look in
// those parts of the struct, so we may continue to get away with it for a
// while...
//extern int _fstat32(int fd, struct stat* buffer);
/*int fstat(int fd, struct stat* buffer)
{
	return _fstat32(fd, buffer);
}
*/
