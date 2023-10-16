
from .common import FILE_TEMPLATE


#================================================================================================

MAGICMETHODS_TEMPLATE = """\
    public class MagicMethods
    {
        public static void
        GetInfo(string field, out string name, out string template, out Type dgtType, out bool needGetSwappedInfo)
        {
            needGetSwappedInfo = false;
            switch (field)
            {
%(normal_cases)s
                default:
                    throw new NotImplementedException(String.Format("unrecognised field: {0}", field));
            }
        }
        
        public static void
        GetSwappedInfo(string field, out string name, out string template, out Type dgtType)
        {
            switch (field)
            {
%(swapped_cases)s
                default:
                    throw new NotImplementedException(String.Format("unrecognised field: {0}", field));
            }
        }
    }"""

MAGICMETHODS_FILE_TEMPLATE = FILE_TEMPLATE % MAGICMETHODS_TEMPLATE


#================================================================================================

MAGICMETHOD_CASE_TEMPLATE = """\
                case nameof(%(c_field)s):%(has_swapped_version_code)s
                    name = "%(py_field)s";
                    dgtType = typeof(dgt_%(dgt_spec)s);
                    template = @"%(template)s";
                    break;"""

SWAP_NO_CODE = ''

SWAP_YES_CODE = """
                    needGetSwappedInfo = true;"""


#================================================================================================

MAGICMETHOD_TEMPLATE2 = """
def {0}(%(arglist)s):
    '''{1}'''
    return _0._dispatcher.%(functype)s('{2}{0}', %(callargs)s)
_ironclad_class_attrs['{0}'] = {0}"""

SQUISHKWARGS_TEMPLATE2 = """
def {0}(self, *args, **kwargs):
    '''{1}'''
    return self._dispatcher.%(functype)s('{2}{0}', self, args, kwargs)
_ironclad_class_attrs['{0}'] = {0}"""

POW_TEMPLATE2 = """
def {0}(self, other, modulo=None):
    '''{1}'''
    return self._dispatcher.%(functype)s('{2}{0}', self, other, modulo)
_ironclad_class_attrs['{0}'] = {0}"""

POW_SWAPPED_TEMPLATE2 = """
def {0}(self, other):
    '''{1}'''
    return self._dispatcher.%(functype)s('{2}{0}', other, self, None)
_ironclad_class_attrs['{0}'] = {0}"""

DELITEM_TEMPLATE2 = """
def {0}(_0, _1):
    '''{1}'''
    return _0._dispatcher.objobjargproc('{2}{0}', _0, _1, None)
_ironclad_class_attrs['{0}'] = {0}"""


#================================================================================================
