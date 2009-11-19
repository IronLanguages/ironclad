
#==========================================================================
# this choice mechanism is obviously stupid, but it's here to remind us
# that this is intended as a source of platform-specific data, and so we
# should be making changes to a specific platform's section, rather than
# just adding code all willy-nilly

TARGET_PLATFORM = 'ironpython'
SOURCE_PLATFORM = 'win32'


#==========================================================================
if TARGET_PLATFORM == 'ironpython' and SOURCE_PLATFORM == 'win32':

    #   ictype code    | actual target platform type
    ICTYPE_2_MGDTYPE = {
        'obj':          'object',
        'ptr':          'IntPtr',
        'str':          'string',
        'void':         'void',
        'char':         'byte',
        'int':          'int',
        'uint':         'uint',
        'long':         'int',
        'ulong':        'uint',
        'llong':        'long',
        'ullong':       'ulong',
        'size':         'uint',
        'ssize':        'int',
        'double':       'double',
        'cpx':          'Py_complex',
    }
    

#==========================================================================
