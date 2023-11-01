

#include "Python.h"

// not included by Python.h, but contain useful declarations/definitions
#include "Python-ast.h"
#include "symtable.h"
#include "structmember.h"
#include "frameobject.h"
#include "pygetopt.h"
#include "pythread.h"
#include "abstract.h"
#include "token.h"
#include "osdefs.h"

// prototypes for managed functions which could be called from C code
#include "_extra_functions.generated.h"

// definitions for missing data
#include "ironclad-data.c"

#pragma clang attribute push (__declspec(dllexport), apply_to=function)

// alternative C implementations of various functions
#include "ironclad-functions.c"

// init function
#include "stubinit.generated.c"

#pragma clang attribute pop

// miscellaneous holes filled
#ifdef _MSC_VER
#include <windows.h>

// _fltused (floating-point used) undefined (Clang/msvcr100 issue only?)
#include <stdint.h>
int32_t _fltused = 0;

// __acrt_iob_func used by MSVCRT 14.0+ headers but not in 10.0
#if _MSC_VER < 1900
extern FILE* __iob_func(void);
FILE* __cdecl __acrt_iob_func(unsigned fd)
{
    return &__iob_func()[fd];
}
#endif

BOOL APIENTRY DllMain(HANDLE hModule,
                      DWORD  ul_reason_for_call,
                      LPVOID lpReserved)
{
    return TRUE;
}
#endif
