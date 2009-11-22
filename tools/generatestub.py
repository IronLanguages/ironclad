
import os, sys

from tools.utils.io import read_lines, read_set, run_generator
from tools.utils.stubgen import StubGenerator
    

#==========================================================================

INPUTS = (
    ('_exported_functions.generated',           read_lines),
    ('_extra_functions',                        read_lines),
    ('_pure_c_symbols',                         read_set),
    ('_mgd_api_data',                           read_lines),
)

OUTPUTS = (
    ('Include/_extra_functions.generated.h',    'HEADER'),
    ('stubinit.generated.c',                    'STUBINIT'),
    ('jumps.generated.asm',                     'JUMPS'),
)

if __name__ == '__main__':
    run_generator(StubGenerator, INPUTS, OUTPUTS)


#==========================================================================
