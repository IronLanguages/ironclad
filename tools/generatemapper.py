
import sys

from tools.utils.file import write
from tools.utils.mapperfilegenerator import MapperFileGenerator

src, dst = sys.argv[1:]
mfg = MapperFileGenerator(src)
for (name, text) in mfg.output.items():
    write(dst, name, text, badge=True)



