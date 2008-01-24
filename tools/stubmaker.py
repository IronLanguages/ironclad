
import os
import sys


class StubMaker(object):

    def __init__(self, sourceLibrary=None, overrideDir=None):
        self.data = []
        self.functions = []
        self.overrides = {}

        self.platform = 'win32'
        if sys.platform.startswith('linux'):
            self.platform = 'linux'

        if sourceLibrary is not None:
            self._read_symbol_table(sourceLibrary)

        if overrideDir is not None:
            self._read_overrides(overrideDir)


    def _read_symbol_table(self, source):
        if self.platform == 'win32':
            self._read_symbol_table_pexports(source)
        else:
            raise NotImplementedError()

    def _read_symbol_table_pexports(self, source):
        f = os.popen("pexports %s" % source)
        try:
            for line in f:
                if line == 'EXPORTS\n':
                    break
            for line in f:
                parts = line[:-1].split(' ')
                if len(parts) == 1:
                    self.functions.append(parts[0])
                else:
                    self.data.append(parts[0])
        finally:
            f.close()


    def _read_overrides(self, overrideDir):
        if not os.path.exists(overrideDir):
            return

        for function in self.functions:
            path = os.path.join(overrideDir, function)
            if os.path.exists(path):
                f = open(path, 'r')
                try:
                    self.overrides[function] = f.read()
                finally:
                    f.close()


    def generate_c(self):
        _includes = '#include <stdio.h>\n#include <stdarg.h>\n#include <stdlib.h>\n\n'
        _declare_data = 'void *%s;\n'
        _boilerplate = '\nvoid *jumptable[%d];\n\nvoid init(void*(*address_getter)(char*)) {\n'
        _init_data = '    %s = address_getter("%s");\n'
        _init_function = '    jumptable[%s] = address_getter("%s");\n'

        result = [_includes]
        result.extend([_declare_data % name for name in self.data])
        result.append(_boilerplate % len(self.functions))
        result.extend([_init_data % (s, s) for s in self.data])
        for i, name in enumerate(self.functions):
            result.append(_init_function % (i, name))
            if self.overrides.has_key(name):
                self.overrides[name] = self.overrides[name] % i
        result.append('}\n\n')
        result.extend(self.overrides.values())
        return ''.join(result)


    def generate_asm(self):
        _header = 'extern _jumptable\n\nsection .code\n\n'
        _declare = 'global _%s\n'
        _define = '_%s:\n    jmp [_jumptable+%d]\n'

        result = [_header]
        implementations = []
        for i, name in enumerate(self.functions):
            if name not in self.overrides:
                result.append(_declare % name)
                implementations.append(_define % (name, i * 4))
        result.append('\n')
        result.extend(implementations)
        return ''.join(result)


    def generate_makefile(self, stubname):
        _library = "%s.dll: asm.o c.o\n\tgcc -shared -o %s.dll asm.o c.o\n"
        _c = "c.o: %s.c\n\tgcc -o c.o -c %s.c\n"
        _asm = "asm.o: %s.asm\n\tnasm -o asm.o -f win32 %s.asm\n"

        return ''.join([
            _library % (stubname, stubname),
            _asm % (stubname, stubname),
            _c % (stubname, stubname),
        ])
