
import os, sys

from tools.utils.apiplumbinggen import ApiPlumbingGenerator
from tools.utils.io import read_args_kwargs, read_gccxml, read_set, run_generator


#==========================================================================

INPUTS = (
    ('_exported_functions.generated',       read_set),
    ('_mgd_api_data',                       read_set),
    ('_mgd_api_structs',                    read_set),
    ('_pure_c_symbols',                     read_set),
    ('_stubmain.generated.xml',             read_gccxml),
    ('_mgd_api_functions',                  read_args_kwargs, 1),
    ('_dispatcher_methods',                 read_args_kwargs, 1, 'data.snippets.cs.dispatcher'),
    ('_dispatcher_fields',                  read_args_kwargs, 3, 'data.snippets.cs.dispatcher'),
    ('_magicmethods',                       read_args_kwargs, 3, 'data.snippets.cs.magicmethods'),
)

OUTPUTS = (
    ('Delegates.Generated.cs',              'DELEGATES'),
    ('Dispatcher.Generated.cs',             'DISPATCHER'),
    ('MagicMethods.Generated.cs',           'MAGICMETHODS'),
    ('PythonApi.Generated.cs',              'PYTHONAPI'),
    ('PythonStructs.Generated.cs',          'PYTHONSTRUCTS'),
)

if __name__ == '__main__':
    run_generator(ApiPlumbingGenerator, INPUTS, OUTPUTS)


#==========================================================================
