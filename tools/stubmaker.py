
import os
import sys

from System.Diagnostics import Process, ProcessStartInfo

def popen(executable, arguments):
    global process # XXX: keep it alive
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
        self.ptr_data = []
        self.static_data = []

        if sourceLibrary is not None:
            self._read_symbol_table(sourceLibrary)

        if overrideDir is not None:
            self._read_overrides(overrideDir)


    def _read_symbol_table(self, source):
        if os.name == 'nt':
            self._read_symbol_table_pexports(source)
        elif os.name == 'posix':
            self._read_symbol_table_objdump(source)
        else:
            print 'Platform', os.name, 'is not supported'
            sys.exit(1)


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
                    self.ptr_data.append(parts[0])
        finally:
            f.close()


    def _read_symbol_table_objdump(self, source):
        f = popen('objdump', '-T %s' % source)
        try:
            for line in f:
                if line.strip() == 'DYNAMIC SYMBOL TABLE:':
                    break
            for line in f:
                line = line.strip()
                if not line:
                    break
                flag = line[15]
                fields = line[17:].split()
                if len(fields) == 3:
                    section, size, name = fields
                if len(fields) == 4:
                    section, size, version, name = fields
                if section not in ('.bss', '.data', '.text'):
                    continue
                if flag == 'F':
                    self.functions.append(name)
                if flag == 'O':
                    self.ptr_data.append(name)
        finally:
            f.close()


    def _read_overrides(self, overrideDir):
        if not os.path.exists(overrideDir):
            return

        ignores = set()
        ignoreFile = os.path.join(overrideDir, "_ignores")
        if os.path.exists(ignoreFile):
            f = open(ignoreFile, 'r')
            try:
                ignores = set([l.rstrip() for l in f.readlines() if l.rstrip()])
            finally:
                f.close()
        self.functions = [f for f in self.functions if f not in ignores]

        staticFile = os.path.join(overrideDir, "_statics")
        if os.path.exists(staticFile):
            f = open(staticFile, 'r')
            try:
                self.static_data = [l.rstrip() for l in f.readlines() if l.rstrip()]
            finally:
                f.close()
        self.ptr_data = [s for s in self.ptr_data if s not in self.static_data and s not in ignores]
                
                
    def generate_c(self):
        _boilerplate = 'void *jumptable[%d];\n\nvoid init(void*(*address_getter)(char*), void(*data_setter)(char*, void*)) {\n'
        _init_ptr_data = '    %s = address_getter("%s");\n'
        _init_static_data = '    data_setter("%s", &%s);\n'
        _init_function = '    jumptable[%s] = address_getter("%s");\n'

        result = [_boilerplate % len(self.functions)]
        result.extend([_init_ptr_data % (s, s) for s in self.ptr_data])
        result.extend([_init_static_data % (s, s) for s in self.static_data])
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

