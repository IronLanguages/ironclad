
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
    exceptions = [dict([("symbol", s)]) for s in read_interesting_lines(EXCEPTIONS_INFILE)]
    exceptions_code = "\n\n".join([EXCEPTION_TEMPLATE % x for x in exceptions])
    write(EXCEPTIONS_OUTFILE, FILE_TEMPLATE % exceptions_code)
    
    type_exceptions = [dict([("symbol", s)]) for s in read_interesting_lines(TYPE_EXCEPTIONS_INFILE)]
    type_exceptions_code = "\n\n".join([TYPE_EXCEPTION_TEMPLATE % x for x in type_exceptions])
    write(TYPE_EXCEPTIONS_OUTFILE, FILE_TEMPLATE % type_exceptions_code)
    
    store_types = [dict([("type", t), ("var", "attempt%d" % i)]) 
                   for (i, t) in enumerate(read_interesting_lines(STORE_INFILE))]
    store_code = STORE_METHOD_TEMPLATE % "\n".join([STORE_TYPE_TEMPLATE % x for x in store_types])
    write(STORE_OUTFILE, FILE_TEMPLATE % store_code)
    
    

EXCEPTIONS_INFILE = "exceptions"
EXCEPTIONS_OUTFILE = "../Python25Mapper_exceptions.cs"
TYPE_EXCEPTIONS_INFILE = "type_exceptions"
TYPE_EXCEPTIONS_OUTFILE = "../Python25Mapper_type_exceptions.cs"
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


