
import sys

from tools.mapperfilegenerator import MapperFileGenerator
from tools.utils import write

src, dst = sys.argv[1:]
mfg = MapperFileGenerator(src)
for (name, text) in mfg.output.items():
    write(dst, name, text, badge=True)



