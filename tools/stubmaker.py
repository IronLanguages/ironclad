
import os

from System.Diagnostics import Process, ProcessStartInfo

def popen(executable, arguments):
    processStartInfo = ProcessStartInfo(executable, arguments)
    processStartInfo.UseShellExecute = False
    processStartInfo.CreateNoWindow = True
    processStartInfo.RedirectStandardOutput = True
    process = Process.Start(processStartInfo)
    return file(process.StandardOutput.BaseStream, "r")


class StubMaker(object):

    def __init__(self, sourceLibrary=None, overrideDir=None):
        self.data = []
        self.functions = []
        self.overrides = {}

        if sourceLibrary is not None:
            self._read_symbol_table(sourceLibrary)

        if overrideDir is not None:
            self._read_overrides(overrideDir)


    def _read_symbol_table(self, source):
        self._read_symbol_table_pexports(source)


    def _read_symbol_table_pexports(self, source):
        f = popen("pexports", source)
        try:
            for line in f:
                if line.strip() == 'EXPORTS':
                    break
            for line in f:
                line = line.strip()
                parts = line.split(' ')
                if len(parts) == 1:
                    self.functions.append(parts[0])
                else:
                    self.data.append(parts[0])
        finally:
            f.close()


    def _read_overrides(self, overrideDir):
        if not os.path.exists(overrideDir):
            return

        def add_override(name):
            path = os.path.join(overrideDir, "%s.c" % name)
            if os.path.exists(path):
                f = open(path, 'r')
                try:
                    self.overrides[name] = f.read().replace('\r\n', '\n')
                finally:
                    f.close()

        for function in self.functions:
            add_override(function)

        for data in self.data:
            add_override(data)


    def generate_c(self):
        _includes = '#include <stdio.h>\n#include <stdarg.h>\n#include <stdlib.h>\n\n'
        _declare_data = 'void *%s;\n'
        _boilerplate = '\nvoid *jumptable[%d];\n\nvoid init(void*(*address_getter)(char*), void(*data_setter)(char*, void*)) {\n'
        _init_ptr_data = '    %s = address_getter("%s");\n'
        _init_custom_data = '    data_setter("%s", &%s);\n'
        _init_function = '    jumptable[%s] = address_getter("%s");\n'

        ptr_data = [s for s in self.data if s not in self.overrides]
        custom_data = [s for s in self.data if s in self.overrides]

        result = [_includes]
        result.extend([_declare_data % s for s in ptr_data])
        result.extend([self.overrides[k] for k in custom_data])
        result.append(_boilerplate % len(self.functions))
        result.extend([_init_ptr_data % (s, s) for s in ptr_data])
        result.extend([_init_custom_data % (s, s) for s in custom_data])
        for i, name in enumerate(self.functions):
            result.append(_init_function % (i, name))
            if self.overrides.has_key(name):
                self.overrides[name] = self.overrides[name] % i
        result.append('}\n\n')
        result.extend([self.overrides[s] for s in self.functions if s in self.overrides])
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
