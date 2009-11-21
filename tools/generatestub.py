
import os, sys

from tools.utils.codegen import filter_keys_uppercase
from tools.utils.io import read_interesting_lines, write
from tools.utils.stubgen import StubGenerator
    

#==========================================================================

def read_all_inputs(src):
    def maybe_read(name):
        try:
            return read_interesting_lines(src, name)
        except:
            return []
    
    EXPORTED_FUNCTIONS = maybe_read("_exported_functions.generated")
    EXTRA_FUNCTIONS = maybe_read("_extra_functions")
    PURE_C_SYMBOLS = set(maybe_read("_pure_c_symbols"))
    MGD_API_DATA = maybe_read("_mgd_api_data")
    
    return filter_keys_uppercase(locals())


#==========================================================================

gen = StubGenerator()

if __name__ == '__main__':
    src, dst = sys.argv[1:]
    inputs = read_all_inputs(src)
    for (path, code) in gen.run(inputs).items():
        write(dst, path, code, badge=True)


#==========================================================================
