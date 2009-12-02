
from itertools import starmap

from data.snippets.cs.mapper import *

from tools.utils.codegen import CodeGenerator, glom_templates, return_dict, starstarmap


#================================================================================================

def _register_slot_template(slot, data):
    template = REGISTER_TYPES_SLOT_TEMPLATES.get(slot, REGISTER_TYPES_DEFAULT_TEMPLATE)
    return template % {
        'slot': slot, 
        'data': data
    }

@return_dict('name type extra')
def _unpack_register_type(name, type, kwargs):
    extra_items = sorted(kwargs.items())
    extra = '\n'.join(starmap(_register_slot_template, extra_items))
    return name, type, extra

def _generate_register_type_method(name, type, **kwargs):
    return REGISTER_TYPES_TEMPLATE % _unpack_register_type(name, type, kwargs)


#================================================================================================

def _generate_file(infos, item_template='%s', file_template=MAPPER_FILE_TEMPLATE, joiner='\n\n'):
    return file_template % glom_templates(joiner, (item_template, infos))


#================================================================================================

class MapperGenerator(CodeGenerator):
    
    INPUTS = '''
        REGISTER_TYPES 
        REGISTER_EXCEPTIONS 
        OPERATOR 
        NUMBERS_C2PY 
        NUMBERS_PY2C STOREDISPATCH
    '''
    
    def _run(self):
        return {
            'REGISTER_TYPES':       _generate_file(
                                        starstarmap(_generate_register_type_method, self.REGISTER_TYPES)),
            'REGISTER_EXCEPTIONS':  _generate_file(
                                        self.REGISTER_EXCEPTIONS, REGISTER_EXCEPTION_TEMPLATE),
            'OPERATOR':             _generate_file(
                                        self.OPERATOR, OPERATOR_TEMPLATE),
            'NUMBERS_C2PY':         _generate_file(
                                        self.NUMBERS_C2PY, NUMBERS_C2PY_TEMPLATE),
            'NUMBERS_PY2C':         _generate_file(
                                        self.NUMBERS_PY2C, NUMBERS_PY2C_TEMPLATE),
            'STOREDISPATCH':        _generate_file(
                                        self.STOREDISPATCH, STOREDISPATCH_TYPE_TEMPLATE, STOREDISPATCH_FILE_TEMPLATE, '\n'),
        }
    

#==========================================================================
