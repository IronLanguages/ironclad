
#====================================================================
# this information is implicit in tools.utils.gccxml
# this set is not used, and not all of the entries in it are handled
# by anything else, but it serves as a note of what util_gccxml can 
# produce

#   ictype           |   comes from actual C language type(s)
_KNOWN_ICTYPES = set((
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

#   ictype         | actual target platform type
ICTYPE_2_MGDTYPE = {
    'obj':          'object',
    'ptr':          'IntPtr',
    'str':          'string',
    'void':         'void',
    'char':         'byte',
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

ICTYPES = set(ICTYPE_2_MGDTYPE.keys())

#====================================================================

ICTYPE_2_NATIVETYPE = {
    'obj': 'ptr',
}

# the following code builds the complete ICTYPE_2_NATIVETYPE so as to avoid
# generating multiple delegate types with identical signatures (these are
# a problem because we can't freely convert between them in C#)

def _invert_dict(dict_):
    bins = {}
    for key, value in dict_.items():
        bin = bins.setdefault(value, [])
        bin.append(key)
    return bins

_ictype_2_mgdtype = dict([
    (k, v) 
    for (k, v) in ICTYPE_2_MGDTYPE.items()
    if k != 'obj'])
mgdtype_2_ictypes = _invert_dict(_ictype_2_mgdtype)

_nativetype_priority = 'int uint long ulong llong ullong'.split()
def _best_nativetype(ictypes):
    if len(ictypes) > 1:
        for good_nativetype in _nativetype_priority:
            if good_nativetype in ictypes:
                return good_nativetype
    return sorted(ictypes)[0]

for _, ictypes in mgdtype_2_ictypes.items():
    nativetype = _best_nativetype(ictypes)
    for ictype in ictypes:
        ICTYPE_2_NATIVETYPE[ictype] = nativetype


#====================================================================
# acceptable types for use in native context

NATIVETYPES = set(ICTYPE_2_NATIVETYPE.values())

NATIVETYPE_2_MGDTYPE = dict([(k, v)
    for (k, v) in ICTYPE_2_MGDTYPE.items()
    if k in NATIVETYPES])
