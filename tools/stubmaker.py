
import os
import sys

from tools.utils import read_interesting_lines


def extract_funcname(c_func):
    # hacka hacka hacka
    return c_func.split('(')[0].split(' ')[-1].replace('*', '')


class StubMaker(object):

    def __init__(self, inputDir=None):
        self.data = set()
        self.ordered_data = []
        self.functions = []
        self.mgd_functions = []
        
        if inputDir is not None:
            self._read_input(inputDir)


    def _read_input(self, inputDir):
        if not os.path.exists(inputDir):
            return

        def tryread(filename):
            path = os.path.join(inputDir, filename)
            if os.path.isfile(path):
                return read_interesting_lines(path)
            return []
        
        self.functions = tryread("_visible_api_functions.generated")
        self.data = set(tryread("_visible_api_data.generated"))
        
        ignores = set(tryread("_dont_register_symbols"))
        self.functions = [f for f in self.functions if f not in ignores]
        
        self.mgd_functions = tryread("_mgd_function_prototypes")
        self.functions.extend(map(extract_funcname, self.mgd_functions))
        
        self.data |= set(tryread("_always_register_data_symbols"))
        self.data -= ignores
        self.ordered_data = tryread("_register_data_symbol_priority")
        self.data -= set(self.ordered_data)
        
                
    def generate_c(self):
        _init_proto = 'void init(void*(*address_getter)(const char*), void(*data_setter)(const char*, const void*))'
        _boilerplate = 'void *jumptable[%%d];\n\n%s {\n' % _init_proto
        _init_data = '    data_setter("%s", &%s);\n'
        _init_function = '    jumptable[%s] = address_getter("%s");\n'

        result = [_boilerplate % len(self.functions)]
        result.extend([_init_data % (s, s) for s in self.ordered_data])
        result.extend([_init_data % (s, s) for s in self.data])
        for i, name in enumerate(self.functions):
            result.append(_init_function % (i, name))
        result.append('}\n')
        return ''.join(result)


    def generate_asm(self):
        _header = 'extern _jumptable\n\nsection .code\n\n'
        _declare = 'global _%s\n'
        _define = '_%s:\n    jmp [_jumptable+%d]\n'

        result = [_header]
        implementations = []
        for i, name in enumerate(self.functions):
            result.append(_declare % name)
            implementations.append(_define % (name, i * 4))
        result.append('\n')
        result.extend(implementations)
        return ''.join(result)

    def generate_header(self):
        return '\n'.join(self.mgd_functions) + '\n'