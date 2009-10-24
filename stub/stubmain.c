
#include "Python.h"

// not included by Python.h, but contain useful declarations/definitions
#include "Python-AST.h"
#include "symtable.h"
#include "structmember.h"
#include "frameobject.h"
#include "pygetopt.h"
#include "abstract.h"
#include "token.h"
#include "osdefs.h"

// prototypes for managed functions called in C code
#include "_mgd_function_prototypes.generated.h"

// definitions for missing data
#include "ironclad-data.c"

// alternative C implementations of various functions
#include "ironclad-functions.c"

// init function
#include "stubinit.generated.c"

