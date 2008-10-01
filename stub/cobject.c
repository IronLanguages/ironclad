


void *
PyCObject_Import(char *module_name, char *name)
{
    PyObject *m, *c;
    void *r = NULL;

    if ((m = PyImport_ImportModule(module_name))) {
        if ((c = PyObject_GetAttrString(m,name))) {
            r = PyCObject_AsVoidPtr(c);
            Py_DECREF(c);
    }
        Py_DECREF(m);
    }
    return r;
}

