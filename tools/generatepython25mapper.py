
import os

def read_interesting_lines(name):
    f = open(name)
    try:
        return [l.rstrip() for l in f.readlines() if l.rstrip()]
    finally:
        f.close()

def write(name, text):
    f = open(name, "w")
    try:
        f.write(text)
    finally:
        f.close()
    

def run():
    exception_kinds = (
        (EXCEPTIONS_INFILE, EXCEPTION_TEMPLATE, EXCEPTIONS_OUTFILE),
        (TYPE_EXCEPTIONS_INFILE, TYPE_EXCEPTION_TEMPLATE, TYPE_EXCEPTIONS_OUTFILE),
        (BUILTIN_EXCEPTIONS_INFILE, BUILTIN_EXCEPTION_TEMPLATE, BUILTIN_EXCEPTIONS_OUTFILE),
    )
    for (infile, template, outfile) in exception_kinds:
        exceptions = [dict([("symbol", s)]) for s in read_interesting_lines(infile)]
        exceptions_code = "\n\n".join([template % x for x in exceptions])
        write(outfile, FILE_TEMPLATE % exceptions_code)
    
    store_types = [dict([("type", t), ("var", "attempt%d" % i)]) 
                   for (i, t) in enumerate(read_interesting_lines(STORE_INFILE))]
    store_code = STORE_METHOD_TEMPLATE % "\n".join([STORE_TYPE_TEMPLATE % x for x in store_types])
    write(STORE_OUTFILE, FILE_TEMPLATE % store_code)
    
    

EXCEPTIONS_INFILE = "exceptions"
EXCEPTIONS_OUTFILE = "../Python25Mapper_exceptions.cs"
TYPE_EXCEPTIONS_INFILE = "type_exceptions"
TYPE_EXCEPTIONS_OUTFILE = "../Python25Mapper_type_exceptions.cs"
BUILTIN_EXCEPTIONS_INFILE = "builtin_exceptions"
BUILTIN_EXCEPTIONS_OUTFILE = "../Python25Mapper_builtin_exceptions.cs"
STORE_INFILE = "store"
STORE_OUTFILE = "../Python25Mapper_store.cs"

FILE_TEMPLATE = """
using System;
using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Types;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
%s
    }
}
"""

EXCEPTION_TEMPLATE = """\
        public override IntPtr Make_PyExc_%(symbol)s()
        {
            return this.Store(PythonExceptions.%(symbol)s);
        }"""

TYPE_EXCEPTION_TEMPLATE = """\
        public override IntPtr Make_PyExc_%(symbol)s()
        {
            return this.Store(TypeCache.%(symbol)s);
        }"""

BUILTIN_EXCEPTION_TEMPLATE = """\
        public override IntPtr Make_PyExc_%(symbol)s()
        {
            return this.Store(Builtin.%(symbol)s);
        }"""

STORE_METHOD_TEMPLATE = """\
        private IntPtr StoreDispatch(object obj)
        {
%s
            return this.StoreObject(obj);
        }"""

STORE_TYPE_TEMPLATE = """\
            %(type)s %(var)s = obj as %(type)s;
            if (%(var)s != null) { return this.Store(%(var)s); }"""


if __name__ == "__main__":
    run()


