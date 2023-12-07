
#================================================================================================

JUMPS_FILE_TEMPLATE = """\
default rel
bits 64

section .bss

global jumptable_addr
jumptable_addr resq 1

section .text

%s
"""

JUMP_DECLARE_TEMPLATE = 'global %(symbol)s'

# This ensures that the first symbol is not exported as DATA
JUMP_START_DEFINE_TEMPLATE = """\

    nop
    nop"""

JUMP_DEFINE_TEMPLATE = """\
%(symbol)s:
    jmp [jumptable_addr+%(offset)d]"""


#================================================================================================

STUBINIT_FILE_TEMPLATE = """\
#ifdef _MSC_VER
    #define DLLEXPORT __declspec(dllexport)
#else
    #define DLLEXPORT
#endif

void *jumptable[%(funccount)d];
extern void *jumptable_addr;

typedef void *(*getfuncptr_fp)(const char*);
typedef void (*registerdata_fp)(const char*, const void*);
DLLEXPORT void init(getfuncptr_fp getfuncptr, registerdata_fp registerdata)
{
    jumptable_addr = jumptable;
%(registerdatas)s
%(getfuncptrs)s
}
"""

STUBINIT_GETFUNCPTR_TEMPLATE = """\
    jumptable[%(index)s] = getfuncptr("%(symbol)s");"""

STUBINIT_REGISTERDATA_TEMPLATE = """\
    registerdata("%(symbol)s", &%(symbol)s);"""


#================================================================================================
