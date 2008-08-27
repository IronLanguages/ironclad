
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
        (BUILTIN_EXCEPTIONS_INFILE, BUILTIN_EXCEPTION_TEMPLATE, BUILTIN_EXCEPTIONS_OUTFILE),
    )
    for (infile, template, outfile) in exception_kinds:
        exceptions = [dict([("symbol", s)]) for s in read_interesting_lines(infile)]
        exceptions_code = "\n\n".join([template % x for x in exceptions])
        write(outfile, FILE_TEMPLATE % exceptions_code)
    
    store_types = [dict([("type", t)]) for t in read_interesting_lines(STORE_INFILE)]
    store_code = STORE_METHOD_TEMPLATE % "\n".join([STORE_TYPE_TEMPLATE % x for x in store_types])
    write(STORE_OUTFILE, FILE_TEMPLATE % store_code)
    
    numbers_pythonsites_types = [dict(zip(("symbol", "site"), line.split())) for line in read_interesting_lines(NUMBERS_PYTHONSITES_INFILE)]
    numbers_pythonsites_code = "\n\n".join([NUMBER_PYTHONSITE_TEMPLATE % x for x in numbers_pythonsites_types])
    write(NUMBERS_PYTHONSITES_OUTFILE, FILE_TEMPLATE % numbers_pythonsites_code)
    
    

EXCEPTIONS_INFILE = "exceptions"
EXCEPTIONS_OUTFILE = "../Python25Mapper_exceptions.Generated.cs"
BUILTIN_EXCEPTIONS_INFILE = "builtin_exceptions"
BUILTIN_EXCEPTIONS_OUTFILE = "../Python25Mapper_builtin_exceptions.Generated.cs"
STORE_INFILE = "store"
STORE_OUTFILE = "../Python25Mapper_store.Generated.cs"
NUMBERS_PYTHONSITES_INFILE = "numbers_pythonsites"
NUMBERS_PYTHONSITES_OUTFILE = "../Python25mapper_numbers_PythonSites.Generated.cs"

FILE_TEMPLATE = """
using System;
using System.Collections;
using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;
using Microsoft.Scripting.Math;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
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
            if (obj is %(type)s) { return this.Store((%(type)s)obj); }"""

NUMBER_PYTHONSITE_TEMPLATE = """\
        public override IntPtr
        %(symbol)s(IntPtr arg1ptr, IntPtr arg2ptr)
        {
            try
            {
                object result = PythonSites.%(site)s(this.Retrieve(arg1ptr), this.Retrieve(arg2ptr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }"""


if __name__ == "__main__":
    run()


