import sys
import os

from tools.utils.subprocess import popen
    

#==========================================================================

class DllReader(object):
    
    def __init__(self, sourceLibrary):
        self.lines = []
        self.data = []
        self.functions = []
        self._read_symbol_table(sourceLibrary)
        self.data.sort()
        self.functions.sort()


    def _read_symbol_table(self, source):
        if os.name == 'nt':
            self._read_symbol_table_pexports(source)
        elif os.name == 'posix':
            self._read_symbol_table_objdump(source)
        else:
            print('Platform', os.name, 'is not supported')
            sys.exit(1)


    def _read_symbol_table_pexports(self, source):
        with popen("pexports", source) as f:
            for line in f:
                self.lines.append(line)
                if line.strip() == 'EXPORTS':
                    break
            for line in f:
                self.lines.append(line)
                line = line.strip()
                parts = line.split(' ')
                if len(parts) == 1:
                    self.functions.append(parts[0])
                else:
                    self.data.append(parts[0])


    def _read_symbol_table_objdump(self, source):
        bitness = 64
        addrlen = bitness // 4
        flagpos = addrlen + 7 # skip a space and first 6 flags
        with popen('objdump', '-T %s' % source) as f:
            for line in f:
                if line.strip() == 'DYNAMIC SYMBOL TABLE:':
                    break
            for line in f:
                line = line.strip()
                if not line:
                    break
                flag = line[flagpos]
                fields = line[flagpos+2:].split() # flagpos + skip the flag and a space (or tab)
                if len(fields) == 3:
                    section, size, name = fields
                if len(fields) == 4:
                    section, size, version, name = fields
                if section not in ('.bss', '.data', '.text'):
                    continue
                if flag == 'F':
                    self.functions.append(name)
                if flag == 'O':
                    self.data.append(name)


#==========================================================================
