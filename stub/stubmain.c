
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
#include "osdefs.h"

// definitions for missing data; alternative C implementations of various functions

#include "ironclad-hacks.c"

// init function

#include "stub.generated.c"

// original c implementations

#include "Objects/abstract.c"
#include "Objects/bufferobject.c"
#include "Objects/cobject.c"
#include "Objects/fileobject.c"
#include "Objects/listobject.c"
#include "Objects/longobject.c"
#include "Objects/methodobject.c"
#include "Objects/object.c"
#include "Objects/stringobject.c"
#include "Objects/structseq.c"
#include "Objects/tupleobject.c"
#include "Objects/unicodeobject.c"

#include "Python/ceval.c"
#include "Python/errors.c"
#include "Python/getargs.c"
#include "Python/modsupport.c"
#include "Python/mysnprintf.c"
#include "Python/mystrtoul.c"
#include "Python/pystrtod.c"
#include "Python/pystate.c"
#include "Python/sigcheck.c"

#include "Parser/intrcheck.c"
#include "Parser/tokenizer.c"

#include "Modules/posixmodule.c"
#include "Modules/mmapmodule.c"
#include "Modules/_csv.c"
#include "Modules/gcmodule.c" // for static definitions only atm


