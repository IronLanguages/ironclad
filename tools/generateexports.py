
import os, sys
from pathlib import Path

from tools.utils.dllreader import DllReader
from tools.utils.io import write


#==========================================================================

if __name__ == '__main__':
    src, dst_api, dst_def = sys.argv[1:]
    dr = DllReader(src)
    write(dst_api, "_exported_functions.generated", '\n'.join(dr.functions), badge=True)
    write(dst_api, "_exported_data.generated", '\n'.join(dr.data), badge=True)
    write(dst_def, Path(src).stem + '.def', ''.join(dr.lines), badge=True)


#==========================================================================
