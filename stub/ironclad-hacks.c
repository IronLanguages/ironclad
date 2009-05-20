

PyTypeObject PyEllipsis_Type;
PyTypeObject PyFrame_Type;
PyTypeObject PyNone_Type;



int
PyEval_GetRestricted(void)
{
	return 0;
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


