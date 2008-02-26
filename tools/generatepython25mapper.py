
import os

def read_interesting_lines(name):
    f = open(name)
    try:
        return [l.rstrip() for l in f.readlines() if l.rstrip()]
    finally:
        f.close()

def run():
    exceptions = [dict([("symbol", p)]) for p in read_interesting_lines("exceptions")]

    exceptions_code = "\n\n".join([METHOD_TEMPLATE % x for x in exceptions])

    output = FILE_TEMPLATE % exceptions_code

    f = open(OUTFILE, "w")
    try:
        f.write(output)
    finally:
        f.close()


OUTFILE = "../Python25Mapper_exceptions.cs"

FILE_TEMPLATE = """
using System;

using IronPython.Runtime.Exceptions;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
%s
    }
}
"""

METHOD_TEMPLATE = """\
        public override IntPtr Make_PyExc_%(symbol)s()
        {
            return this.Store(ExceptionConverter.GetPythonException("%(symbol)s"));
        }"""


if __name__ == "__main__":
    run()


