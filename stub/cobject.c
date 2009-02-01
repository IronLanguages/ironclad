
/* Declarations for objects of type PyCObject */

typedef void (*destructor1)(void *);
typedef void (*destructor2)(void *, void*);

typedef struct {
    PyObject_HEAD
    void *cobject;
    void *desc;
    void (*destructor)(void *);
} PyCObject;

void *
PyCObject_GetDesc(PyObject *self)
{
    if (self) {
        if (self->ob_type == &PyCObject_Type)
            return ((PyCObject *)self)->desc;
        PyErr_SetString(PyExc_TypeError,
                        "PyCObject_GetDesc with non-C-object");
    }
    if (!PyErr_Occurred())
        PyErr_SetString(PyExc_TypeError,
                        "PyCObject_GetDesc called with null pointer");
    return NULL;
}


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

