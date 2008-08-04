

/* Shorthands to return certain errors */

static PyObject *
type_error(const char *msg, PyObject *obj)
{
	PyErr_Format(PyExc_TypeError, msg, obj->ob_type->tp_name);
	return NULL;
}

static PyObject *
null_error(void)
{
	if (!PyErr_Occurred())
		PyErr_SetString(PyExc_SystemError,
				"null argument to internal routine");
	return NULL;
}

static PyObject*
call_function_tail(PyObject *callable, PyObject *args)
{
    PyObject *retval;

    if (args == NULL)
        return NULL;

    if (!PyTuple_Check(args)) {
        PyObject *a;

        a = PyTuple_New(1);
        if (a == NULL) {
            Py_DECREF(args);
            return NULL;
        }
        PyTuple_SET_ITEM(a, 0, args);
        args = a;
    }
    retval = PyObject_Call(callable, args, NULL);

    Py_DECREF(args);

    return retval;
}

PyObject *
PyObject_CallFunction(PyObject *callable, char *format, ...)
{
    va_list va;
    PyObject *args;

    if (callable == NULL)
        return null_error();

    if (format && *format) {
        va_start(va, format);
        args = Py_VaBuildValue(format, va);
        va_end(va);
    }
    else
        args = PyTuple_New(0);

    return call_function_tail(callable, args);
}

PyObject *
_PyObject_CallFunction_SizeT(PyObject *callable, char *format, ...)
{
	va_list va;
	PyObject *args;

	if (callable == NULL)
		return null_error();

	if (format && *format) {
		va_start(va, format);
		args = _Py_VaBuildValue_SizeT(format, va);
		va_end(va);
	}
	else
		args = PyTuple_New(0);

	return call_function_tail(callable, args);
}

PyObject *
PyObject_CallMethod(PyObject *o, char *name, char *format, ...)
{
	va_list va;
	PyObject *args;
	PyObject *func = NULL;
	PyObject *retval = NULL;

	if (o == NULL || name == NULL)
		return null_error();

	func = PyObject_GetAttrString(o, name);
	if (func == NULL) {
		PyErr_SetString(PyExc_AttributeError, name);
		return 0;
	}

	if (!PyCallable_Check(func)) {
		type_error("attribute of type '%.200s' is not callable", func); 
		goto exit;
	}

	if (format && *format) {
		va_start(va, format);
		args = Py_VaBuildValue(format, va);
		va_end(va);
	}
	else
		args = PyTuple_New(0);

	retval = call_function_tail(func, args);

  exit:
	/* args gets consumed in call_function_tail */
	Py_XDECREF(func);

	return retval;
}

PyObject *
_PyObject_CallMethod_SizeT(PyObject *o, char *name, char *format, ...)
{
	va_list va;
	PyObject *args;
	PyObject *func = NULL;
	PyObject *retval = NULL;

	if (o == NULL || name == NULL)
		return null_error();

	func = PyObject_GetAttrString(o, name);
	if (func == NULL) {
		PyErr_SetString(PyExc_AttributeError, name);
		return 0;
	}

	if (!PyCallable_Check(func)) {
		type_error("attribute of type '%.200s' is not callable", func); 
		goto exit;
	}

	if (format && *format) {
		va_start(va, format);
		args = _Py_VaBuildValue_SizeT(format, va);
		va_end(va);
	}
	else
		args = PyTuple_New(0);

	retval = call_function_tail(func, args);

  exit:
	/* args gets consumed in call_function_tail */
	Py_XDECREF(func);

	return retval;
}
