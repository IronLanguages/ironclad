
from itertools import starmap

from data.snippets.cs.mapper import *

from tools.utils.codegen import CodeGenerator, glom_templates, return_dict, starstarmap


#================================================================================================

def _fill_slot_template(slot, data):
    template = FILL_TYPES_SLOT_TEMPLATES.get(slot, FILL_TYPES_DEFAULT_TEMPLATE)
    return template % {
        'slot': slot, 
        'data': data
    }

@return_dict('name type extra')
def _unpack_fill_type(name, type, kwargs):
    extra_items = sorted(kwargs.items())
    extra = '\n'.join(starmap(_fill_slot_template, extra_items))
    return name, type, extra

def _generate_fill_type_method(name, type, **kwargs):
    return FILL_TYPES_TEMPLATE % _unpack_fill_type(name, type, kwargs)


#================================================================================================

def _generate_file(infos, item_template='%s', file_template=MAPPER_FILE_TEMPLATE, joiner='\n\n'):
    return file_template % glom_templates(joiner, (item_template, infos))


#================================================================================================

class MapperGenerator(CodeGenerator):
    
    INPUTS = 'FILL_TYPES EXCEPTIONS OPERATOR NUMBERS_C2PY NUMBERS_PY2C STOREDISPATCH'
    
    def _run(self):
        return {
            'FILL_TYPES':       _generate_file(
                                    starstarmap(_generate_fill_type_method, self.FILL_TYPES)),
            'EXCEPTIONS':       _generate_file(
                                    self.EXCEPTIONS, EXCEPTION_TEMPLATE),
            'OPERATOR':         _generate_file(
                                    self.OPERATOR, OPERATOR_TEMPLATE),
            'NUMBERS_C2PY':     _generate_file(
                                    self.NUMBERS_C2PY, NUMBERS_C2PY_TEMPLATE),
            'NUMBERS_PY2C':     _generate_file(
                                    self.NUMBERS_PY2C, NUMBERS_PY2C_TEMPLATE),
            'STOREDISPATCH':    _generate_file(
                                    self.STOREDISPATCH, STOREDISPATCH_TYPE_TEMPLATE, STOREDISPATCH_FILE_TEMPLATE, '\n'),
        }
    

#==========================================================================
