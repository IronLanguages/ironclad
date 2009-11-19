
from tools.utils.platform import ICTYPE_2_MGDTYPE


#==========================================================================

def _invert_dict(dict_):
    bins = {}
    for key, value in dict_.items():
        bin = bins.setdefault(value, [])
        bin.append(key)
    return bins

def _choose_best_name(equivalents, priority):
    if len(equivalents) > 1:
        for good_choice in priority:
            if good_choice in equivalents:
                return good_choice
    return sorted(equivalents)[0]

def _get_equivalent_key_mapping(d, priority=''):
    equivalent_keys = _invert_dict(d).values()
    result = {}
    for keys in equivalent_keys:
        best = _choose_best_name(keys, priority.split())
        for key in keys:
            result[key] = best
    return result


#==========================================================================
# extract useful information about platform types

VALID_ICTYPES = set(ICTYPE_2_MGDTYPE.keys())

EQUIVALENT_ICTYPES = _get_equivalent_key_mapping(
    ICTYPE_2_MGDTYPE, priority='int uint long ulong llong ullong')


#==========================================================================
# as you will have observed, multiple ictypes can map to the same 
# managed type. canonicalisation avoids confusion, and also prevents
# the creation of multiple identical delegate types

def canonical_ictype(ictype):
    return EQUIVALENT_ICTYPES[ictype]


#==========================================================================
# note that 'obj' refers to a PyObject*: so, when we're dealing with 
# native types, we want to use arguments of type 'ptr'
# 
# we need the distinction for when we're generating the Dispatcher
# classes; it allows us to automatically translate managed objects
# to PyObject*s and vice versa, while passing other pointer types
# through unchanged

def native_ictype(ictype):
    return {'obj': 'ptr'}.get(ictype, ictype)


#==========================================================================
# on a similar note, sometimes we don't want to automatically marshal
# strings and would prefer to pass raw pointers

def unstringed_ictype(ictype):
    return {'str': 'ptr'}.get(ictype, ictype)


#==========================================================================
# appendix: not actually used
# here is every distinct type of which we are aware; we can plausibly 
# expect utils_gccxml functions to emit type codes from the following set

#   ictype          |   comes from actual C language type(s)
ALL_ICTYPES = set((
    'obj',          #   Py(*?)Object* 
    'str',          #   (const?) char*
    'ptr',          #   (other)* 
    'void',         #   void
    'bool',         #   bool
    'char',         #   char
    'wchar',        #   wchar
    'ucchar',       #   Py_UNICODE
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
    

#==========================================================================
