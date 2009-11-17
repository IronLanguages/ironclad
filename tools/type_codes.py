
#====================================================================
# this information is implicit in tools.utils_gccxml
# this set is not used, and not all of the entries in it are handled
# by anything else, but it serves as a note of what util_gccxml can 
# produce

#   ctype           |   comes from actual C language type(s)
_KNOWN_CTYPES = set((
    'obj',          #   Py(*?)Object* 
    'str',          #   (const?) char*
    'ptr',          #   (other)* 
    'void',         #   void
    'bool',         #   bool
    'char',         #   char
    'wchar',        #   wchar
    'uchar',        #   Py_UNICODE
    'int',          #   int
    'uint',         #   unsigned int
    'long',         #   long
    'llong',        #   unsigned long
    'ulong',        #   long long
    'ullong',       #   unsigned long long
    'size',         #   size_t
    'ssize',        #   Py_ssize_t
    'double',       #   double
    'cpx',          #   Py_complex
))

#====================================================================
# this is specific to C# with 32-bit python

#   ctype         | actual target platform type
CTYPE_2_MGDTYPE = {
    'obj':          'object',
    'ptr':          'IntPtr',
    'str':          'string',
    'void':         'void',
    'int':          'int',
    'uint':         'uint',
    'long':         'int',
    'ulong':        'uint',
    'llong':        'long',
    'ullong':       'ulong',
    'size':         'uint',
    'ssize':        'int',
    'double':       'double',
    'cpx':          'Py_complex',
}

CTYPES = set(CTYPE_2_MGDTYPE.keys())

#====================================================================
# delegates wrap unmanaged calls, which always take pointers (not objects)

CTYPE_2_DGTTYPE = {
    'obj': 'ptr',
}

# the following code builds the rest of CTYPE_2_DGTTYPE so as to avoid
# generating multiple delegate types with identical signatures (these are
# a problem because we can't freely convert between them in C#)

def _invert_dict(dict_):
    bins = {}
    for key, value in dict_.items():
        bin = bins.setdefault(value, [])
        bin.append(key)
    return bins

ctype_2_mgdtype_copy = dict(CTYPE_2_MGDTYPE)
del ctype_2_mgdtype_copy['obj']
mgdtype_2_ctypes = _invert_dict(ctype_2_mgdtype_copy)

_ctype_priority = 'int uint long ulong llong ullong'.split()
def _choose_ctype(ctypes):
    if len(ctypes) > 1:
        for preferred_name in _ctype_priority:
            if preferred_name in ctypes:
                return preferred_name
    return sorted(ctypes)[0]

for _, ctypes in mgdtype_2_ctypes.items():
    best = _choose_ctype(ctypes)
    for ctype in ctypes:
        CTYPE_2_DGTTYPE[ctype] = best


#====================================================================
# acceptable types for use in dgt_specs

DGTTYPES = set(CTYPE_2_DGTTYPE.values())

DGTTYPE_2_MGDTYPE = dict([(k, v)
    for (k, v) in CTYPE_2_MGDTYPE.items()
    if k in DGTTYPES])
