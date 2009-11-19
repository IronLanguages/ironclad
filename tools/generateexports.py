
import os, sys

from tools.utils.dllreader import DllReader
from tools.utils.io import write


#==========================================================================

if __name__ == '__main__':
    src, dst = sys.argv[1:]
    dr = DllReader(src)
    
    write(dst, "_exported_functions.generated", '\n'.join(dr.functions), badge=True)
    write(dst, "_exported_data.generated", '\n'.join(dr.data), badge=True)

