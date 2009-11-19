
import sys

from tools.utils.io import write
from tools.utils.mapperfilegen import MapperFileGenerator


#==========================================================================

if __name__ == '__main__':
    src, dst = sys.argv[1:]
    mfg = MapperFileGenerator(src)
    
    for (name, text) in mfg.output.items():
        write(dst, name, text, badge=True)



