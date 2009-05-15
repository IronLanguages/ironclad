
/* External interface to call any callable object.
   The arg must be a tuple or NULL. */

#undef PyEval_CallObject
/* for backward compatibility: export this interface */

PyObject *
PyEval_CallObject(PyObject *func, PyObject *arg)
{
	return PyEval_CallObjectWithKeywords(func, arg, (PyObject *)NULL);
}
#define PyEval_CallObject(func,arg) \
        PyEval_CallObjectWithKeywords(func, arg, (PyObject *)NULL)

PyObject *
PyEval_CallObjectWithKeywords(PyObject *func, PyObject *arg, PyObject *kw)
{
	PyObject *result;

	if (arg == NULL) {
		arg = PyTuple_New(0);
		if (arg == NULL)
			return NULL;
	}
	else if (!PyTuple_Check(arg)) {
		PyErr_SetString(PyExc_TypeError,
				"argument list must be a tuple");
		return NULL;
	}
	else
		Py_INCREF(arg);

	if (kw != NULL && !PyDict_Check(kw)) {
		PyErr_SetString(PyExc_TypeError,
				"keyword list must be a dictionary");
		Py_DECREF(arg);
		return NULL;
	}

	result = PyObject_Call(func, arg, kw);
	Py_DECREF(arg);
	return result;
}

int
PyEval_GetRestricted(void)
{
	// Ironclad
	return 0;

	PyFrameObject *current_frame = PyEval_GetFrame();
	return current_frame == NULL ? 0 : PyFrame_IsRestricted(current_frame);
}
