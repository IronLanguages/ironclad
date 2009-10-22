

type_codes = {
    # special
    'void': # no return value, or no args
        'void',
    'str': # char*s; marshalled into strings
        'string',
    'obj': # PyFoo*s; needs to be stored/retrieved/cleaned up
        'object',
    'cpx': # Py_complex, defined in PythonStructs.cs
        'Py_complex',
    
    # platform-specific C types
    'ptr': # unknown ptr types; not translated
        'IntPtr',
    'size': # Py_ssize_t
        'uint',
    'int': # int
        'int',
    'long': # long
        'int',
    'llong': # long long
        'long',
    'uint': # unsigned int
        'uint',
    'ulong': # unsigned long
        'uint',
    'ullong': # unsigned long long
        'ulong',
    'double': # double
        'double',
}

