import os
import sys

if sys.platform == 'win32':
    platform = 'win32'
elif sys.platform.startswith('linux'):
    platform = 'linux'


def skip_to(f, string):
    for line in f:
        if string in line:
            break


class JumpyLibrary:

    def __init__(self, library):
        self.library = library
        self.objects = []
        self.functions = []
        self.implementations = {}

    def generate(self):
        self.read_symbol_table()
        self.generate_file('jumptable.c', self.generate_jumptable_c)
        self.generate_file('jumptable.asm', self.generate_jumptable_asm)
        os.chdir('build')
        os.system('make -f Makefile-%s' % platform)
        os.chdir(os.pardir)

    def generate_file(self, filename, func):
        path = os.path.join('build', filename)
        f = open(path, 'w')
        f.writelines(func())
        f.close()

    def read_symbol_table(self):
        if platform == 'linux':
            self.read_symbol_table_objdump()
        else:
            self.read_symbol_table_pexports()
        for i, name in enumerate(self.functions):
            impl = self.get_implementation(i, name)
            if impl:
                self.implementations[name] = impl

    def read_symbol_table_objdump(self):
        f = os.popen('objdump -T %s' % self.library)
        skip_to(f, 'DYNAMIC SYMBOL TABLE')
        for line in f:
            if not line.strip():
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
                self.objects.append(name)
        self.functions.sort()
        self.objects.sort()

    def read_symbol_table_pexports(self):
        f = os.popen('pexports %s' % self.library)
        skip_to(f, 'EXPORTS')
        for line in f:
            fields = line.split()
            if len(fields) == 1:
                name, = fields
                self.functions.append(name)
            if len(fields) == 2:
                name, type = fields
                assert type == 'DATA'
                self.objects.append(name)

    def get_implementation(self, i, funcname):
        path = os.path.join('implementations', funcname)
        if not os.path.exists(path):
            return ''
        f = open(path, 'r')
        try:
            return f.read() % i
        finally:
            f.close()

    def generate_jumptable_c(self):
        lines = []
        line = lines.append
        line('#include <stdio.h>\n')
        line('#include <stdarg.h>\n')
        line('#include <stdlib.h>\n')

        for name in self.objects:
            line('void *%s;\n' % name)

        line('\nvoid *jumptable[%d];\n\n' % len(self.functions))
        line('void init(void*(*address_getter)(char*)) {\n')

        for name in self.objects:
            line('\t%s = address_getter("%s");\n' % (name, name))

        for i, name in enumerate(self.functions):
            line('\tjumptable[%d] = address_getter("%s");\n' % (i, name))
        line('}\n')

        lines.extend(self.implementations.values())
        return lines

    def generate_jumptable_asm(self):
        jumptable = '_jumptable'
        if platform == 'linux':
            jumptable = 'jumptable'
        lines = []
        line = lines.append
        line('extern %s\n' % jumptable)
        line('section .code\n')
        for name in self.functions:
            if name not in self.implementations:
                if platform == 'linux':
                    line('global %s:function\n' % name)
                else:
                    line('global _%s\n' % name)
        for i, name in enumerate(self.functions):
            if name not in self.implementations:
                offset = i * 4
                line('_%s:\n' % name)
                line('\tjmp [%s+%d]\n' % (jumptable, offset))
        return lines

if __name__ == '__main__':
    library = JumpyLibrary(r'C:\WINDOWS\system32\python24.dll')
    if platform == 'linux':
        library = JumpyLibrary('/usr/lib/libpython2.5.so')
    library.generate()
