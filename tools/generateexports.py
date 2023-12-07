
import os, sys

from tools.utils.dllreader import DllReader
from tools.utils.io import write


#==========================================================================

if __name__ == '__main__':
    src, dst_api, dst_def = sys.argv[1:]
    dr = DllReader(src)
    write(dst_api, "_exported_functions.generated", '\n'.join(dr.functions), badge=True)
    write(dst_api, "_exported_data.generated", '\n'.join(dr.data), badge=True)
    # On non-Windows OSes, python.def will not be a DEF file but an objdump log file.
    # It is not used further in the build process but still useful to inspect if needed.
    write(dst_def, "python.def", ''.join(dr.lines), badge=True)


#==========================================================================
