

void
PyErr_SetObject(PyObject *exception, PyObject *value)
{
	Py_XINCREF(exception);
	Py_XINCREF(value);
	PyErr_Restore(exception, value, (PyObject *)NULL);
}

void
PyErr_SetNone(PyObject *exception)
{
	PyErr_SetObject(exception, (PyObject *)NULL);
}

void
PyErr_SetString(PyObject *exception, const char *string)
{
	PyObject *value = PyString_FromString(string);
	PyErr_SetObject(exception, value);
	Py_XDECREF(value);
}

PyObject *
PyErr_Format(PyObject *exception, const char *format, ...)
{
	va_list vargs;
	PyObject* string;

#ifdef HAVE_STDARG_PROTOTYPES
	va_start(vargs, format);
#else
	va_start(vargs);
#endif

	string = PyString_FromFormatV(format, vargs);
	PyErr_SetObject(exception, string);
	Py_XDECREF(string);
	va_end(vargs);
	return NULL;
}


int
PyErr_ExceptionMatches(PyObject *exc)
{
	return PyErr_GivenExceptionMatches(PyErr_Occurred(), exc);
}


int
PyErr_GivenExceptionMatches(PyObject *err, PyObject *exc)
{
	if (err == NULL || exc == NULL) {
		/* maybe caused by "import exceptions" that failed early on */
		return 0;
	}
	if (PyTuple_Check(exc)) {
		Py_ssize_t i, n;
		n = PyTuple_Size(exc);
		for (i = 0; i < n; i++) {
			/* Test recursively */
		     if (PyErr_GivenExceptionMatches(
			     err, PyTuple_GET_ITEM(exc, i)))
		     {
			     return 1;
		     }
		}
		return 0;
	}
	/* err might be an instance, so check its class. */
	if (PyExceptionInstance_Check(err))
		err = PyExceptionInstance_Class(err);

	if (PyExceptionClass_Check(err) && PyExceptionClass_Check(exc)) {
		/* problems here!?  not sure PyObject_IsSubclass expects to
		   be called with an exception pending... */
		return PyObject_IsSubclass(err, exc);
	}

	return err == exc;
}



void
PyErr_Restore(PyObject *type, PyObject *value, PyObject *traceback)
{
    PyThreadState *tstate = PyThreadState_GET();
    PyObject *oldtype, *oldvalue, *oldtraceback;

    if (traceback != NULL && !PyTraceBack_Check(traceback)) {
        /* XXX Should never happen -- fatal error instead? */
        /* Well, it could be None. */
        Py_DECREF(traceback);
        traceback = NULL;
    }

    /* Save these in locals to safeguard against recursive
       invocation through Py_XDECREF */
    oldtype = tstate->curexc_type;
    oldvalue = tstate->curexc_value;
    oldtraceback = tstate->curexc_traceback;

    tstate->curexc_type = type;
    tstate->curexc_value = value;
    tstate->curexc_traceback = traceback;

    Py_XDECREF(oldtype);
    Py_XDECREF(oldvalue);
    Py_XDECREF(oldtraceback);
}


PyObject *
PyErr_Occurred(void)
{
    PyThreadState *tstate = PyThreadState_GET();

    return tstate->curexc_type;
}

void
PyErr_Fetch(PyObject **p_type, PyObject **p_value, PyObject **p_traceback)
{
    PyThreadState *tstate = PyThreadState_GET();

    *p_type = tstate->curexc_type;
    *p_value = tstate->curexc_value;
    *p_traceback = tstate->curexc_traceback;

    tstate->curexc_type = NULL;
    tstate->curexc_value = NULL;
    tstate->curexc_traceback = NULL;
}

void
PyErr_Clear(void)
{
    PyErr_Restore(NULL, NULL, NULL);
}

