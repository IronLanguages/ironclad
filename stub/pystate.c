
PyObject *
PyThreadState_GetDict(void)
{
	if (_PyThreadState_Current == NULL)
		return NULL;

	if (_PyThreadState_Current->dict == NULL) {
		PyObject *d;
		_PyThreadState_Current->dict = d = PyDict_New();
		if (d == NULL)
			PyErr_Clear();
	}
	return _PyThreadState_Current->dict;
}

PyThreadState *
PyThreadState_Get(void)
{
	if (_PyThreadState_Current == NULL)
		Py_FatalError("PyThreadState_Get: no current thread");

	return _PyThreadState_Current;
}


PyThreadState *
PyThreadState_Swap(PyThreadState *newts)
{
	PyThreadState *oldts = _PyThreadState_Current;

	_PyThreadState_Current = newts;
	/* debug-only code omitted for ironclad */
	return oldts;
}


