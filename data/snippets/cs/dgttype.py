
DGTTYPE_TEMPLATE = """\
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate %(rettype)s dgt_%(name)s(%(arglist)s);
"""