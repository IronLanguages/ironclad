
import os, sys
from itertools import starmap

from tools.utils import read, read_interesting_lines, write


def stitch_default(snippets):
    return '\n\n'.join(snippets)

def stitch_store(snippets):
    return STORE_METHOD_TEMPLATE % "\n".join(snippets)


def forever_split(s):
    for part in s.split(): yield part
    while True: yield ''

def extract_columns(raw_data, columns, template):
    def extract(line):
        return  template % dict(zip(columns, forever_split(line)))
    return map(extract, raw_data)


def fill_slot_template(slot, data):
    template = FILL_TYPES_SLOT_TEMPLATES.get(slot, FILL_TYPES_DEFAULT_TEMPLATE)
    return template % {'slot': slot, 'data': data}

def maybe_eval_dict(container):
    if not container: return ''
    _dict = eval(container[0])
    return '\n'.join(starmap(fill_slot_template, sorted(_dict.items())))
        
def extract_fill_type(raw_data, template):
    snippets = []
    for line in raw_data:
        _input = line.split(None, 2)
        _dict = {'name': _input[0], 'type': _input[1], 'extra': maybe_eval_dict(_input[2:])}
        snippets.append(template % _dict)
    return snippets


class MapperFileGenerator(object):
    
    def __init__(self, src):
        self.src = src
        self.output = {}
        self.run()
    
    def generate_mapper_file(self, srcname, *args, **kwargs):
        src = os.path.join(self.src, srcname)
        dstname = 'PythonMapper%s.Generated.cs' % srcname
        stitch=kwargs.get('stitch', '\n\n'.join)
        extract=kwargs.get('extract', extract_columns)
        
        snippets = extract(read_interesting_lines(src), *args)
        self.output[dstname] = MAPPER_FILE_TEMPLATE % stitch(snippets)
    
    def run(self):
        self.generate_mapper_file("_exceptions",
            ('name',), EXCEPTION_TEMPLATE)
        
        self.generate_mapper_file("_operator",
            ("name", "operator"), OPERATOR_TEMPLATE)
        
        self.generate_mapper_file("_numbers_convert_c2py",
            ("name", "type", "cast"), C2PY_TEMPLATE)
        
        self.generate_mapper_file("_numbers_convert_py2c",
            ("name", "converter", "type", "default", "coerce"), PY2C_TEMPLATE)
        
        self.generate_mapper_file("_store_dispatch",
            ('type',), STORE_TYPE_TEMPLATE,
            stitch=stitch_store)
        
        self.generate_mapper_file("_fill_types",
            FILL_TYPES_TEMPLATE,
            extract=extract_fill_type)



MAPPER_FILE_TEMPLATE = """
using System;
using System.Collections;
using System.Runtime.InteropServices;
using IronPython.Modules;
using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;
using Microsoft.Scripting.Math;
using Ironclad.Structs;

namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
%s
    }
}
"""

EXCEPTION_TEMPLATE = """\
        public override void Fill_PyExc_%(name)s(IntPtr addr)
        {
            IntPtr value = this.Store(PythonExceptions.%(name)s);
            CPyMarshal.WritePtr(addr, value);
        }"""

STORE_METHOD_TEMPLATE = """\
        private IntPtr StoreDispatch(object obj)
        {
%s
            return this.StoreObject(obj);
        }"""

STORE_TYPE_TEMPLATE = """\
            if (obj is %(type)s) { return this.StoreTyped((%(type)s)obj); }"""

OPERATOR_TEMPLATE = """\
        public override IntPtr
        %(name)s(IntPtr arg1ptr, IntPtr arg2ptr)
        {
            try
            {
                object result = PythonOperator.%(operator)s(this.scratchContext, this.Retrieve(arg1ptr), this.Retrieve(arg2ptr));
                return this.Store(result);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }"""

C2PY_TEMPLATE = """\
        public override IntPtr
        %(name)s(%(type)s value)
        {
            return this.Store(%(cast)svalue);
        }"""

PY2C_TEMPLATE = """\
        public override %(type)s
        %(name)s(IntPtr valuePtr)
        {
            try
            {
                return this.%(converter)s(this.Retrieve(valuePtr))%(coerce)s;
            }
            catch (Exception e)
            {
                this.LastException = e;
                return %(default)s;
            }
        }"""

FILL_TYPES_TEMPLATE = """\
        public override void
        Fill_%(name)s(IntPtr ptr)
        {
            CPyMarshal.Zero(ptr, Marshal.SizeOf(typeof(PyTypeObject)));
            CPyMarshal.WriteIntField(ptr, typeof(PyTypeObject), "ob_refcnt", 1);
%(extra)s
            this.map.Associate(ptr, %(type)s);
        }"""

FILL_TYPES_NUMBER_TEMPLATE = """\
            this.%(data)s(ptr);"""

FILL_TYPES_SIZE_TEMPLATE = """\
            CPyMarshal.WriteIntField(ptr, typeof(PyTypeObject), "%(slot)s", Marshal.SizeOf(typeof(%(data)s)));"""

FILL_TYPES_DEFAULT_TEMPLATE = """\
            CPyMarshal.WritePtrField(ptr, typeof(PyTypeObject), "%(slot)s", this.GetAddress("%(data)s"));"""

FILL_TYPES_SLOT_TEMPLATES = {
    "tp_as_number": FILL_TYPES_NUMBER_TEMPLATE,
    "tp_basicsize": FILL_TYPES_SIZE_TEMPLATE,
    "tp_itemsize": FILL_TYPES_SIZE_TEMPLATE,
}