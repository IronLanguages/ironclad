
#================================================================================================

JUMPS_FILE_TEMPLATE = """\
default rel
bits 64

section .bss

global jumptable
jumptable resq %(funccount)d

section .text

%(code)s
"""

JUMP_DECLARE_TEMPLATE = 'global %(symbol)s'

# This ensures that the first symbol is not exported as DATA
JUMP_START_DEFINE_TEMPLATE = """\

    nop
    nop"""

JUMP_DEFINE_TEMPLATE = """\
%(symbol)s:
    jmp [jumptable+%(offset)d]"""


#================================================================================================

STUBINIT_FILE_TEMPLATE = """\
#ifdef _MSC_VER
    #define DLLEXPORT __declspec(dllexport)
#else
    #define DLLEXPORT
#endif

extern void *jumptable[];

typedef void *(*getfuncptr_fp)(const char*);
typedef void (*registerdata_fp)(const char*, const void*);
DLLEXPORT void init(getfuncptr_fp getfuncptr, registerdata_fp registerdata)
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
