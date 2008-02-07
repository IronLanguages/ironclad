
int PyArg_ParseTupleAndKeywords(void *args, void *kwargs, char *format, void *kwlist, ...)
{
    va_list ap;
    va_start(ap, kwlist);
    // I should never need more pointers than len(format)...
    void **varargs = (void**)calloc((strlen(format) + 1), sizeof(void*));
    int in = 0;
    int out = 0;

    while (format[in] != ':' && format[in] != 0)
    {
        if (format[in] == '|')
        {
            ++in;
        }
        varargs[out] = va_arg(ap, void*);
        ++in;
        ++out;
    }
    va_end(ap);
    
    int (*mgd_PyArg_ParseTupleAndKeywords)(void*, void*, char*, void*, void**) = 
        (int(*)(void*, void*, char*, void*, void**))(jumptable[%d]);
        
    int result = mgd_PyArg_ParseTupleAndKeywords(args, kwargs, format, kwlist, varargs);
    free(varargs);
    return result;
}
