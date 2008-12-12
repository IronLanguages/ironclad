
PyObject *
PyLong_FromVoidPtr(void *p)
{
#if SIZEOF_VOID_P <= SIZEOF_LONG
	if ((long)p < 0)
		return PyLong_FromUnsignedLong((unsigned long)p);
	return PyInt_FromLong((long)p);
#else

#ifndef HAVE_LONG_LONG
#   error "PyLong_FromVoidPtr: sizeof(void*) > sizeof(long), but no long long"
#endif
#if SIZEOF_LONG_LONG < SIZEOF_VOID_P
#   error "PyLong_FromVoidPtr: sizeof(PY_LONG_LONG) < sizeof(void*)"
#endif
	/* optimize null pointers */
	if (p == NULL)
		return PyInt_FromLong(0);
	return PyLong_FromUnsignedLongLong((unsigned PY_LONG_LONG)p);

#endif /* SIZEOF_VOID_P <= SIZEOF_LONG */
}

/* Get a C pointer from a long object (or an int object in some cases) */

void *
PyLong_AsVoidPtr(PyObject *vv)
{
	/* This function will allow int or long objects. If vv is neither,
	   then the PyLong_AsLong*() functions will raise the exception:
	   PyExc_SystemError, "bad argument to internal function"
	*/
#if SIZEOF_VOID_P <= SIZEOF_LONG
	long x;

	if (PyInt_Check(vv))
		x = PyInt_AS_LONG(vv);
	else if (PyLong_Check(vv) && _PyLong_Sign(vv) < 0)
		x = PyLong_AsLong(vv);
	else
		x = PyLong_AsUnsignedLong(vv);
#else

#ifndef HAVE_LONG_LONG
#   error "PyLong_AsVoidPtr: sizeof(void*) > sizeof(long), but no long long"
#endif
#if SIZEOF_LONG_LONG < SIZEOF_VOID_P
#   error "PyLong_AsVoidPtr: sizeof(PY_LONG_LONG) < sizeof(void*)"
#endif
	PY_LONG_LONG x;

	if (PyInt_Check(vv))
		x = PyInt_AS_LONG(vv);
	else if (PyLong_Check(vv) && _PyLong_Sign(vv) < 0)
		x = PyLong_AsLongLong(vv);
	else
		x = PyLong_AsUnsignedLongLong(vv);

#endif /* SIZEOF_VOID_P <= SIZEOF_LONG */

	if (x == -1 && PyErr_Occurred())
		return NULL;
	return (void *)x;
}
