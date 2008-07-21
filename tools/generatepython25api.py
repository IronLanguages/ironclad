
import os

def read_interesting_lines(name):
    f = open(name)
    try:
        return [l.rstrip() for l in f.readlines() if l.rstrip()]
    finally:
        f.close()

def run():
    not_implemented_methods_set = set(read_interesting_lines(FUNCTIONS_FILE))
    method_files = [f for f in os.listdir(".") if f.endswith(DELEGATE_EXT)]

    methods = []
    for f in method_files:
        return_type, arglist, code = read_interesting_lines(f)
        symbol = f[:-len(DELEGATE_EXT)]
        not_implemented_methods_set.remove(symbol)
        methods.append({
            "symbol": symbol,
            "return_type": return_type,
            "arglist": arglist,
            "code": code
        })
        
    not_implemented_methods = [{"symbol": s} for s in not_implemented_methods_set]
    
    methods_code_list = [METHOD_TEMPLATE % x for x in methods]
    methods_code_list.extend([NOT_IMPL_METHOD_TEMPLATE % x for x in not_implemented_methods])
    methods_code = "\n\n".join(methods_code_list)
    
    methods_switch_list = [METHOD_CASE % x for x in methods]
    methods_switch_list.extend([NOT_IMPL_METHOD_CASE % x for x in not_implemented_methods])
    methods_switch = "\n".join(methods_switch_list)

    ptr_data_items = [dict([("symbol", p)]) for p in read_interesting_lines(DATA_PTR_ITEMS_FILE)]

    ptr_data_items_code = "\n\n".join([PTR_DATA_ITEM_TEMPLATE % x for x in ptr_data_items])
    ptr_data_items_switch = "\n".join([PTR_DATA_ITEM_CASE % x for x in ptr_data_items])

    data_items = []
    for p in read_interesting_lines(DATA_ITEMS_FILE):
        symbol, _type = p.split(" ")
        data_items.append({"symbol": symbol, "type": _type})

    data_items_code = "\n\n".join([DATA_ITEM_TEMPLATE % x for x in data_items])
    data_items_switch = "\n".join([DATA_ITEM_CASE % x for x in data_items])

    output = FILE_TEMPLATE % (
        methods_code,
        ptr_data_items_code,
        methods_switch,
        ptr_data_items_switch,
        data_items_code,
        data_items_switch
    )

    f = open(OUTFILE, "w")
    try:
        f.write(output)
    finally:
        f.close()

FUNCTIONS_FILE = "python25ApiFunctions"
DATA_ITEMS_FILE = "python25ApiDataItems"
DATA_PTR_ITEMS_FILE = "python25ApiDataPtrItems"

DELEGATE_EXT = ".pmdi"
OUTFILE = "../Python25Api.cs"

FILE_TEMPLATE = """
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using Ironclad.Structs;

namespace Ironclad
{

    public class Python25Api
    {
        protected Dictionary<string, Delegate> dgtMap = new Dictionary<string, Delegate>();
        private Dictionary<string, IntPtr> dataMap = new Dictionary<string, IntPtr>();
    
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate void CPython_null_Delegate();

%s

%s

        public virtual IntPtr GetAddress(string name)
        {
            if (this.dgtMap.ContainsKey(name))
            {
                return Marshal.GetFunctionPointerForDelegate(this.dgtMap[name]);
            }

            switch (name)
            {
%s
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
        
NOT_IMPL_METHOD_TEMPLATE = """\
        public void %(symbol)s()
        {
            throw new NotImplementedException("called %(symbol)s -- stack is probably corrupt now");
        }"""
        
METHOD_CASE = """\
                case "%(symbol)s":
                    this.dgtMap[name] = new %(symbol)s_Delegate(this.%(symbol)s);
                    break;"""
                    
NOT_IMPL_METHOD_CASE = """\
                case "%(symbol)s":
                    this.dgtMap[name] = new CPython_null_Delegate(this.%(symbol)s);
                    break;"""

PTR_DATA_ITEM_TEMPLATE = """\
        public virtual IntPtr Make_%(symbol)s() { return IntPtr.Zero; }
        public IntPtr %(symbol)s
        {
            get
            {
                return this.dataMap["%(symbol)s"];
            }
        }"""

PTR_DATA_ITEM_CASE = """\
                case "%(symbol)s":
                    this.dataMap[name] = this.Make_%(symbol)s();
                    return this.dataMap[name];"""

DATA_ITEM_TEMPLATE = """\
        public virtual void Fill_%(symbol)s(IntPtr address) { ; }
        public IntPtr %(symbol)s
        {
            get
            {
                IntPtr address;
                if (this.dataMap.TryGetValue("%(symbol)s", out address))
                {
                    return address;
                }
                return IntPtr.Zero;
            }
        }"""

DATA_ITEM_CASE = """\
                case "%(symbol)s":
                    CPyMarshal.Zero(address, Marshal.SizeOf(typeof(%(type)s)));
                    this.Fill_%(symbol)s(address);
                    this.dataMap["%(symbol)s"] = address;
                    break;"""


if __name__ == "__main__":
    run()


