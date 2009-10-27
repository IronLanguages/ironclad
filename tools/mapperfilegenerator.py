
import os, sys
from itertools import starmap

from tools.utils import eval_dict_item, read, read_interesting_lines, write

from data.snippets.cs.pythonmapper import *

#================================================================================================

def stitch_default(snippets):
    return '\n\n'.join(snippets)

def stitch_store(snippets):
    return STORE_METHOD_TEMPLATE % "\n".join(snippets)

#================================================================================================

def forever_split(s):
    for part in s.split(): yield part
    while True: yield ''

def extract_columns(raw_data, columns, template):
    def extract(line):
        return  template % dict(zip(columns, forever_split(line)))
    return map(extract, raw_data)

#================================================================================================

def fill_slot_template(slot, data):
    template = FILL_TYPES_SLOT_TEMPLATES.get(slot, FILL_TYPES_DEFAULT_TEMPLATE)
    return template % {'slot': slot, 'data': data}
        
def extract_fill_type(raw_data):
    snippets = []
    for line in raw_data:
        _input = line.split(None, 2)
        _dict = {
            'name': _input[0],
            'type': _input[1],
            'extra': eval_dict_item(_input[2:]) or ''
        }
        if _dict['extra']:
            _dict['extra'] = '\n'.join(starmap(fill_slot_template, sorted(_dict['extra'].items())))
        snippets.append(FILL_TYPES_TEMPLATE % _dict)
    return snippets

#================================================================================================

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
        self.output[dstname] = PYTHONMAPPER_FILE_TEMPLATE % stitch(snippets)
    
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
            extract=extract_fill_type)

