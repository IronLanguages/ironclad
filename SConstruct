

#===============================================================================
# Various useful functions

import operator, os, sys

def splitstring(f):
    def g(_, s):
        if isinstance(s, basestring):
            s = s.split()
        return f(_, s)
    return g

@splitstring
def glommap(f, inputs):
    return reduce(operator.add, map(f, inputs), [])

@splitstring
def pathmap(base, files):
    return map(lambda x: os.path.join(base, x), files)

@splitstring
def submap(template, inserts):
    return map(lambda x: template % x, inserts)

def source_appender(appendee):
    def append(target, source, env):
        return target, source + appendee
    return append

#===============================================================================
# PLATFORM-SPECIFIC GLOBALS

WIN32 = sys.platform == 'win32'

if WIN32:
    #==================================================================
    # These variables will be needed on any platform, I think
    
    ASFLAGS = '-f win32'
    CSC = 'C:\\windows\\Microsoft.NET\\Framework\\v2.0.50727\\csc.exe'
    CSC_CMD = '$CSC /nologo /out:$TARGET /t:library $REFERENCES $SOURCES'
    IPY = '"C:\\Program Files\\IronPython 2.6\\ipy.exe"'
    IPY_DIR = '"C:\\Program Files\\IronPython 2.6"'
    IPY_REF_TEMPLATE = '/r:$IPY_DIR\\%s.dll'
    NATIVE_TOOLS = ['mingw', 'nasm']
    PYTHON_DLL = '"C:\\windows\\system32\\python26.dll"'
    
    #==================================================================
    # These variables should only be necessary on win32
    
    COPY_CMD = 'copy $SOURCE $TARGET'
    DLLTOOL_CMD = 'dlltool -D $NAME -d $SOURCE -l $TARGET'
    LINK_MSVCR90_FLAGS = '-specs=stub/use-msvcr90.spec'
    MINGW_LIB = 'C:\\Program Files\\MinGW\\lib' # TODO: surely we can find this one out from the tools choice somehow..?
    MSVCR90_DLL = 'C:\\Windows\\winsxs\\x86_Microsoft.VC90.CRT_1fc8b3b9a1e18e3b_9.0.21022.8_x-ww_d08d0375\\msvcr90.dll'
    PEXPORTS_CMD = 'pexports $SOURCE > $TARGET'
    RES_CMD = 'windres --input $SOURCE --output $TARGET --output-format=coff'


#===============================================================================
# PLATFORM-AGNOSTIC GLOBALS
# If any turn out to need to be platform-specific, please move them

COMPILE_IRONCLAD_FLAGS = '-DIRONCLAD -DPy_BUILD_CORE'
INSERT_CMD = '$IPY tools/insertfiles.py $SOURCES > $TARGET'
OBJ_CMD = '$CC $CCFLAGS -o $TARGET -c $SOURCE'
DLL_CMD = '$CC $CCFLAGS -shared -o $TARGET $SOURCES'
PYTHON26OBJ_CMD = OBJ_CMD + ' -I$CPPPATH'
PYTHON26DLL_CMD = DLL_CMD + ' -export-all-symbols'
COMMON = dict(IPY=IPY, IPY_DIR=IPY_DIR)


#===============================================================================
#===============================================================================
# This section builds the CLR part
#===============================================================================

managed = Environment(CSC=CSC, **COMMON)
ipy_dlls = 'IronPython IronPython.Modules Microsoft.Dynamic Microsoft.Scripting Microsoft.Scripting.Core'
ipy_refs = ' '.join(map(lambda x: IPY_REF_TEMPLATE % x, ipy_dlls.split()))
managed['BUILDERS']['Dll'] = Builder(action=CSC_CMD, REFERENCES=ipy_refs)
managed['BUILDERS']['Insert'] = Builder(action=INSERT_CMD)

#===============================================================================
# Generated code: note whole heaps of ugly explicit dependencies

tools_sources = (
    'dispatcherinputs.py dispatchersnippets.py generatedispatcher.py platform.py '
    '_mgd_api_functions _mgd_api_functions _all_api_functions')
dispatcher_sources = pathmap('tools', tools_sources) + pathmap('stub', '_mgd_functions _ignore_symbols')
dispatcher_basenames = 'Delegates Dispatcher MagicMethods Python25Api'
dispatcher_outputs = pathmap('src', submap('%s.Generated.cs', dispatcher_basenames))
managed.Command(dispatcher_outputs, dispatcher_sources, '$IPY tools/generatedispatcher.py src')

mapper_basenames = 'exceptions fill_types numbers_convert_c2py numbers_convert_py2c operator store_dispatch'.split()
mapper_sources = pathmap('src/python25mapper_components', mapper_basenames)
mapper_outputs = pathmap('src', map((lambda x: 'Python25Mapper_%s.Generated.cs' % x), mapper_basenames))
managed.Command(mapper_outputs, mapper_sources, '$IPY tools/generatepython25mapper.py src/python25mapper_components src')

def CodeSnippet(name, src):
    target = 'src/CodeSnippets_%s.Generated.cs' % name
    sources = pathmap('src/python25mapper_components', [('CodeSnippets_%s.cs.src' % name), ('%s.py' % src)])
    managed.Insert(target, sources)
CodeSnippet('ihooks', 'import_code')
CodeSnippet('kindaDictProxy', 'kindadictproxy')
CodeSnippet('kindaSeqIter', 'kindaseqiter')

# Build the actual managed library
managed.Dll('build/ironclad/ironclad.dll', Glob('src/*.cs'))


#===============================================================================
#===============================================================================
# This section builds all the unmanaged parts
# (python26.dll, ic_msvcr90.dll, several test files)
#===============================================================================

native = Environment(tools=NATIVE_TOOLS, ASFLAGS=ASFLAGS, PYTHON_DLL=PYTHON_DLL, **COMMON)
native['BUILDERS']['Obj'] = Builder(action=OBJ_CMD, suffix='.o')
native['BUILDERS']['Python26Obj'] = Builder(action=PYTHON26OBJ_CMD, suffix='.o', CCFLAGS=COMPILE_IRONCLAD_FLAGS, CPPPATH='stub/Include')
native['BUILDERS']['Dll'] = Builder(action=DLL_CMD, suffix='.dll')
native['BUILDERS']['Python26Dll'] = native['BUILDERS']['Dll']

if WIN32:
    # If, RIGHT NOW*, no backup of libmsvcr90.a exists, create one
    # * At runtime, not at build time
    
    in_mingw_lib = lambda x: os.path.join(MINGW_LIB, x)
    original, backup = map(in_mingw_lib, ['libmsvcr90.a', 'libmsvcr90.a.orig'])
    if os.path.exists(original) and not os.path.exists(backup):
        print 
        print 'Hi! Building Ironclad will patch your MinGW install. The affected file will be moved safely out of the way.'
        print 'Should you ever need to restore your MinGW install to its original state, just execute the following command:'
        print
        print '  copy "%s" "%s"' % (backup, original)
        print
        raw_input('Enter to accept, ^C to cancel:')
        import shutil
        shutil.move(original, backup)
        
    
    # Brutally patch mingw/lib/libmsvcr90.a
    native.Command('stub/msvcr90.def', MSVCR90_DLL, PEXPORTS_CMD)
    patch_importlib = native.Command(original, 'stub/msvcr90.def', DLLTOOL_CMD, NAME='msvcr90.dll')
    native.NoClean(patch_importlib)
    
    # This resource needs to be embedded in several C libraries, so winsxs doesn't get huffy at runtime
    depend_msvcr90 = native.Command('stub/depend-msvcr90.res', 'stub/depend-msvcr90.rc', RES_CMD)
    native.Depends(depend_msvcr90, 'stub/depend-msvcr90.manifest')
    native.Depends(depend_msvcr90, patch_importlib)
    
    # These builders should ensure that their targets correctly link with msvcr90.dll
    append_depend = source_appender(depend_msvcr90)
    native['BUILDERS']['Msvcr90Dll'] = Builder(
        action=DLL_CMD, suffix='.dll', emitter=append_depend, CCFLAGS=LINK_MSVCR90_FLAGS)
    native['BUILDERS']['Python26Dll'] = Builder(
        action=PYTHON26DLL_CMD, suffix='.dll', emitter=append_depend, CCFLAGS=LINK_MSVCR90_FLAGS)

#===============================================================================
# Unmanaged libraries for build/ironclad

# Generate stub code
buildstub_sources = pathmap('stub', '_ordered_data _mgd_functions _ignore_symbols _extra_data')
buildstub_outputs = pathmap('stub', 'jumps.generated.asm stubinit.generated.c')
native.Command(buildstub_outputs, buildstub_sources, '$IPY tools/buildstub.py $PYTHON_DLL stub stub')

# Compile stub code
# NOTE: nasm Object seems to work fine out of the box
# TODO: use scanner instead of explicit dependency for stubmain.c?
jumps_obj = native.Object('stub/jumps.generated.asm')
stubmain_obj = native.Python26Obj('stub/stubmain.c')
Depends(stubmain_obj, pathmap('stub', 'stubinit.generated.c ironclad-data.c ironclad-functions.c'))

# Build and link python26.dll
cpy_src_dirs = 'Modules Objects Parser Python'
cpy_srcs = glommap(lambda x: Glob('stub/%s/*.c' % x), cpy_src_dirs)
cpy_objs = glommap(native.Python26Obj, cpy_srcs)
native.Python26Dll('build/ironclad/python26.dll', stubmain_obj + jumps_obj + cpy_objs)

if WIN32:
    # This dll redirects various msvcr90 functions so we can DllImport them in C#
    native.Msvcr90Dll('build/ironclad/ic_msvcr90.dll', native.Obj('stub/ic_msvcr90.c'))

#===============================================================================
# Test data

native.Dll('tests/data/setvalue.pyd', native.Obj('tests/data/src/setvalue.c'))
native.Dll('tests/data/exportsymbols', native.Obj('tests/data/src/exportsymbols.c'))
native.Dll('tests/data/fakepython25', native.Obj('tests/data/src/fakepython25.c'))

if WIN32:
    # Some tests will load and unload dlls which depend on msvcr90; if msvcr90's ref count
    # hits 0 and it gets reloaded, bad things happen. The test framework loads this dll, and
    # keeps it loaded, to prevent aforesaid bad things.
    native.Msvcr90Dll('tests/data/implicit-load-msvcr90', native.Obj('tests/data/src/empty.c'))
