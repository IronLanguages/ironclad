
int PyArg_ParseTuple(void *args, char *format, ...)
{
    va_list ap;
    va_start(ap, format);
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

    int (*mgd_PyArg_ParseTuple)(void*, char*, void**) =
        (int(*)(void*, char*, void**))(jumptable[%d]);

    int result = mgd_PyArg_ParseTuple(args, format, varargs);
    free(varargs);
    return result;
}
