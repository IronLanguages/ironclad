
import os, sys
from itertools import starmap

from data.snippets.cs.pythonmapper import *

from tools.utils.codegen import eval_kwargs_column
from tools.utils.io import read, read_interesting_lines, write


#================================================================================================

def stitch_storedispatch(snippets):
    return STOREDISPATCH_TEMPLATE % "\n".join(snippets)


#================================================================================================

def _forever_split(s):
    for part in s.split(): yield part
    while True: yield ''

def extract_columns(raw_data, columns, template):
    def extract(line):
        return  template % dict(zip(columns, _forever_split(line)))
    return map(extract, raw_data)


#================================================================================================

def _fill_slot_template(slot, data):
    template = FILL_TYPES_SLOT_TEMPLATES.get(slot, FILL_TYPES_DEFAULT_TEMPLATE)
    return template % {'slot': slot, 'data': data}
        
def extract_fill_type(raw_data):
    snippets = []
    for line in raw_data:
        _input = line.split(None, 2)
        _dict = {
            'name': _input[0],
            'type': _input[1],
            'extra': eval_kwargs_column(_input[2:]) or ''
        }
        if _dict['extra']:
            _dict['extra'] = '\n'.join(starmap(_fill_slot_template, sorted(_dict['extra'].items())))
        snippets.append(FILL_TYPES_TEMPLATE % _dict)
    return snippets


#================================================================================================

class MapperFileGenerator(object):
    
    def __init__(self, src):
        self.src = src
        self.output = {}
        self.run()
    
    def _generate_mapper_file_code(self, srcname, *args, **kwargs):
        src = os.path.join(self.src, srcname)
        dstname = 'PythonMapper%s.Generated.cs' % srcname
        stitch=kwargs.get('stitch', '\n\n'.join)
        extract=kwargs.get('extract', extract_columns)
        
        snippets = extract(read_interesting_lines(src), *args)
        self.output[dstname] = PYTHONMAPPER_FILE_TEMPLATE % stitch(snippets)
    
    def run(self):
        self._generate_mapper_file_code("_exceptions",
            ('name',), EXCEPTION_TEMPLATE)
        
        self._generate_mapper_file_code("_operator",
            ("name", "operator"), OPERATOR_TEMPLATE)
        
        self._generate_mapper_file_code("_numbers_c2py",
            ("name", "type", "cast"), C2PY_TEMPLATE)
        
        self._generate_mapper_file_code("_numbers_py2c",
            ("name", "converter", "type", "default", "coerce"), PY2C_TEMPLATE)
        
        self._generate_mapper_file_code("_storedispatch",
            ('type',), STOREDISPATCH_TYPE_TEMPLATE,
            stitch=stitch_storedispatch)
        
        self._generate_mapper_file_code("_fill_types",
            extract=extract_fill_type)
    

#==========================================================================
