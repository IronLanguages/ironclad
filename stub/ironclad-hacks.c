

PyTypeObject PyNotImplemented_Type;
PyTypeObject PyEllipsis_Type;
PyTypeObject PyNone_Type;



int
PyEval_GetRestricted(void)
{
	return 0;
}


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

