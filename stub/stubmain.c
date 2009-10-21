
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

// alternative C implementations of various functions
#include "ironclad-functions.c"

// definitions for missing data
#include "ironclad-data.c"

// init function
#include "stubinit.generated.c"

