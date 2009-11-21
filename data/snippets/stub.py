
#================================================================================================

JUMPS_FILE_TEMPLATE = """\
extern _jumptable

section .code

%s
"""

JUMP_DECLARE_TEMPLATE = 'global _%(symbol)s'

JUMP_DEFINE_TEMPLATE = """\
_%(symbol)s:
    jmp [_jumptable+%(offset)d]"""


#================================================================================================

STUBINIT_FILE_TEMPLATE = """\
void *jumptable[%(funccount)d];

typedef void *(*getfuncptr_fp)(const char*);
typedef void (*registerdata_fp)(const char*, const void*);
void init(getfuncptr_fp getfuncptr, registerdata_fp registerdata)
{
%(registerdatas)s
%(getfuncptrs)s
}
"""

STUBINIT_GETFUNCPTR_TEMPLATE = """\
    jumptable[%(index)s] = getfuncptr("%(symbol)s");"""

STUBINIT_REGISTERDATA_TEMPLATE = """\
    registerdata("%(symbol)s", &%(symbol)s);"""


#================================================================================================
