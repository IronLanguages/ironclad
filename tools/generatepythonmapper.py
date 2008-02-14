
import os

def read_interesting_lines(name):
    f = open(name)
    try:
        return [l.rstrip() for l in f.readlines() if l.rstrip()]
    finally:
        f.close()

def run():
    method_files = [f for f in os.listdir(".") if f.endswith(DELEGATE_EXT)]

    methods = []
    for f in method_files:
        return_type, arglist, code = read_interesting_lines(f)
        methods.append({
            "symbol": f[:-len(DELEGATE_EXT)],
            "return_type": return_type,
            "arglist": arglist,
            "code": code
        })

    methods_code = "\n\n".join([METHOD_TEMPLATE % x for x in methods])
    methods_switch = "\n".join([METHOD_CASE % x for x in methods])

    properties = [dict([("symbol", p)]) for p in read_interesting_lines("pythonMapperDataItems")]

    properties_code = "\n\n".join([PROPERTY_TEMPLATE % x for x in properties])
    properties_switch = "\n".join([PROPERTY_CASE % x for x in properties])

    output = FILE_TEMPLATE % (
        methods_code,
        methods_switch,
        properties_code,
        properties_switch
    )

    f = open(OUTFILE, "w")
    try:
        f.write(output)
    finally:
        f.close()


DELEGATE_EXT = ".pythonMapperDelegateItem"
OUTFILE = "../PythonMapper.cs"

FILE_TEMPLATE = """
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

namespace JumPy
{

    public class PythonMapper
    {
        private Dictionary<string, Delegate> dgtMap = new Dictionary<string, Delegate>();
        private Dictionary<string, IntPtr> dataMap = new Dictionary<string, IntPtr>();

%s

        public IntPtr GetAddress(string name)
        {
            if (this.dgtMap.ContainsKey(name))
            {
                return Marshal.GetFunctionPointerForDelegate(this.dgtMap[name]);
            }

            switch (name)
            {
%s

                default:
                    return IntPtr.Zero;
            }
            return Marshal.GetFunctionPointerForDelegate(this.dgtMap[name]);
        }


%s

        public void SetData(string name, IntPtr address)
        {
            switch (name)
            {
%s
            }
        }
    }
}
"""

METHOD_TEMPLATE = """\
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate %(return_type)s %(symbol)s_Delegate(%(arglist)s);
        public virtual %(return_type)s %(symbol)s(%(arglist)s)
        {
            %(code)s;
        }"""

METHOD_CASE = """\
                case "%(symbol)s":
                    this.dgtMap[name] = new %(symbol)s_Delegate(this.%(symbol)s);
                    break;"""

PROPERTY_TEMPLATE = """\
        public virtual void Fill_%(symbol)s(IntPtr address) { ; }
        public IntPtr %(symbol)s
        {
            get
            {
                return this.dataMap["%(symbol)s"];
            }
        }"""

PROPERTY_CASE = """\
                case "%(symbol)s":
                    this.Fill_%(symbol)s(address);
                    this.dataMap["%(symbol)s"] = address;
                    break;"""


if __name__ == "__main__":
    run()


