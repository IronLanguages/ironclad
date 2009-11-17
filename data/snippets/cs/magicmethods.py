
from common import FILE_TEMPLATE

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
%s
                default:
                    throw new NotImplementedException(String.Format("unrecognised field: {0}", field));
            }
        }
        
        public static void
        GetSwappedInfo(string field, out string name, out string template, out Type dgtType)
        {
            switch (field)
            {
%s
                default:
                    throw new NotImplementedException(String.Format("unrecognised field: {0}", field));
            }
        }
    }"""

MAGICMETHODS_FILE_TEMPLATE = FILE_TEMPLATE % MAGICMETHODS_TEMPLATE

#================================================================================================

MAGICMETHOD_CASE = """\
                case "%s":
                    name = "%s";%s
                    dgtType = typeof(dgt_%s);
                    template = @"%s";
                    break;"""

MAGICMETHOD_NEEDSWAP_NO = ''

MAGICMETHOD_NEEDSWAP_YES = """
                    needGetSwappedInfo = true;"""

#================================================================================================

MAGICMETHOD_TEMPLATE_TEMPLATE = """
def {0}(%(arglist)s):
    '''{1}'''
    return _0._dispatcher.%(functype)s('{2}{0}', %(callargs)s)
_ironclad_class_attrs['{0}'] = {0}"""

POW_TEMPLATE_TEMPLATE = """
def {0}(self, other, modulo=None):
    '''{1}'''
    return self._dispatcher.%(functype)s('{2}{0}', self, other, modulo)
_ironclad_class_attrs['{0}'] = {0}"""

POW_SWAPPED_TEMPLATE_TEMPLATE = """
def {0}(self, other):
    '''{1}'''
    return self._dispatcher.%(functype)s('{2}{0}', other, self, None)
_ironclad_class_attrs['{0}'] = {0}"""

SQUISHKWARGS_TEMPLATE_TEMPLATE = """
def {0}(self, *args, **kwargs):
    '''{1}'''
    return self._dispatcher.%(functype)s('{2}{0}', self, args, kwargs)
_ironclad_class_attrs['{0}'] = {0}"""
