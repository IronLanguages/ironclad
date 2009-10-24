
import os, sys

from tools.stubmaker import StubMaker
from tools.utils import write

src_dll, src, dst = sys.argv[1:]
dst_include = os.path.join(dst, 'Include')

if not os.path.exists(dst): os.mkdir(dst)
if not os.path.exists(dst_include): os.mkdir(dst_include)

sm = StubMaker(src_dll, src)
write(dst, "stubinit.generated.c", sm.generate_c())
write(dst, "jumps.generated.asm", sm.generate_asm())
write(dst_include, "_mgd_function_prototypes.generated.h", sm.generate_header())

