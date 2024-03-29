
from tools.utils.codegen import scrunch_filename
from tools.utils.io import read_args_kwargs, read_cols, run_generator
from tools.utils.mappergen import MapperGenerator


#==========================================================================

INPUTS = (
    ('_register_types',         read_args_kwargs, 2),
    ('_register_exceptions',    read_cols, 'name source'),
    ('_operator',               read_cols, 'name operator'),
    ('_numbers_c2py',           read_cols, 'name type cast'),
    ('_numbers_py2c',           read_cols, 'name converter type default coerce'),
    ('_storedispatch',          read_cols, 'type'),
)

def _output_name(name):
    return 'PythonMapper%s.Generated.cs' % name, scrunch_filename(name)
OUTPUTS = list(map(_output_name, [input[0] for input in INPUTS]))

if __name__ == '__main__':
    run_generator(MapperGenerator, INPUTS, OUTPUTS)


#==========================================================================
