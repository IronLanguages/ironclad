
from .common import FILE_TEMPLATE


#================================================================================================

CODESNIPPETS_TEMPLATE = """\
    internal class CodeSnippets
    {
%s
    }"""

CODESNIPPETS_FILE_TEMPLATE = FILE_TEMPLATE % CODESNIPPETS_TEMPLATE


#================================================================================================

CODESNIPPET_TEMPLATE = """\
        public const string %(name)s = @"%(code)s";"""


#================================================================================================
