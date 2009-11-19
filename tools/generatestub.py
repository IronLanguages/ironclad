
import os, sys

from tools.utils.io import write
from tools.utils.stubmaker import StubMaker

#==========================================================================

if __name__ == '__main__':
    src, dst = sys.argv[1:]
    dst_include = os.path.join(dst, 'Include')
    sm = StubMaker(src)
    
    write(dst, "stubinit.generated.c", sm.generate_c(), badge=True)
    write(dst, "jumps.generated.asm", sm.generate_asm(), badge=True)
    write(dst_include, "_extra_functions.generated.h", sm.generate_header(), badge=True)

