

PyObject *
PyTuple_GetItem(register PyObject *op, register Py_ssize_t i)
{
	if (!PyTuple_Check(op)) {
		PyErr_BadInternalCall();
		return NULL;
	}
	if (i < 0 || i >= ((PyTupleObject *)op) -> ob_size) {
		PyErr_SetString(PyExc_IndexError, "tuple index out of range");
		return NULL;
	}
	return ((PyTupleObject *)op) -> ob_item[i];
}

int
PyTuple_SetItem(register PyObject *op, register Py_ssize_t i, PyObject *newitem)
{
	register PyObject *olditem;
	register PyObject **p;
	if (!PyTuple_Check(op) || op->ob_refcnt != 1) {
		Py_XDECREF(newitem);
		PyErr_BadInternalCall();
		return -1;
	}
	if (i < 0 || i >= ((PyTupleObject *)op) -> ob_size) {
		Py_XDECREF(newitem);
		PyErr_SetString(PyExc_IndexError,
				"tuple assignment index out of range");
		return -1;
	}
	p = ((PyTupleObject *)op) -> ob_item + i;
	olditem = *p;
	*p = newitem;
	Py_XDECREF(olditem);
	return 0;
}
