
import os, sys

dst = sys.argv[1]

from tools.apiwrangler import ApiWrangler
from tools.dispatcherinputs import WRANGLER_INPUT
from tools.utils import write

wrangler = ApiWrangler(WRANGLER_INPUT)

def write_output(key, name):
    dstname = name + '.Generated.cs'
    write(dst, dstname, wrangler.output[key], badge=True)

write_output('magicmethods_code', 'MagicMethods')
write_output('pythonapi_code', 'PythonApi')
write_output('dispatcher_code', 'Dispatcher')
write_output('dgttype_code', 'Delegates')

