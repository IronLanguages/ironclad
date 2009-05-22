
// force build-as-if-building-Python-itself

#define Py_BUILD_CORE

// enable ironclad-related tweaks

#define IRONCLAD


#include "Python.h"

// not included by Python.h, but contain useful declarations/definitions

#include "Python-AST.h"
#include "symtable.h"
#include "structmember.h"
#include "frameobject.h"
#include "pygetopt.h"
#include "abstract.h"
#include "token.h"

// definitions for missing data; alternative C implementations of various functions

#include "ironclad-hacks.c"

// init function

#include "stub.generated.c"

// c implementations

#include "abstract.c"
#include "ceval.c"
#include "cobject.c"
#include "errors.c"
#include "getargs.c"
#include "modsupport.c"
#include "mysnprintf.c"
#include "mystrtoul.c"
#include "object.c"
#include "pystrtod.c"
#include "stringobject.c"
#include "tupleobject.c"
#include "bufferobject.c"
#include "methodobject.c"
#include "longobject.c"
#include "listobject.c"
#include "pystate.c"
#include "pythonrun.c"
#include "fileobject.c"
#include "unicodeobject.c"
#include "tokenizer.c"
#include "objimpl.c"

// builtin modules

#include "mmapmodule.c"
#include "_csv.c"
