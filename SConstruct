#===============================================================================
# Various useful functions

import operator, os, sys
from SCons.Scanner.C import CScanner

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


#===============================================================================
# PLATFORM-SPECIFIC GLOBALS

WIN32 = sys.platform == 'win32'

if WIN32:
    #==================================================================
    # These variables will be needed on any platform, I think
    
    ASFLAGS = '-f win32'
    CSC = r'C:\windows\Microsoft.NET\Framework\v2.0.50727\csc.exe'
    CSC_CMD = '$CSC /nologo /out:$TARGET /t:library $REFERENCES $SOURCES'
    GCCXML_CC1PLUS = r'"C:\Program Files\GCC_XML\bin\gccxml_cc1plus.exe"'
    IPY = r'"C:\Program Files\IronPython 2.6\ipy.exe"'
    IPY_DIR = r'"C:\Program Files\IronPython 2.6"'
    IPY_REF_TEMPLATE = r'/r:$IPY_DIR\%s.dll'
    NATIVE_TOOLS = ['mingw', 'nasm']
    PYTHON_DLL = r'C:\windows\system32\python26.dll'
    
    OBJ_SUFFIX = '.o'
    DLL_SUFFIX = '.dll'
    MGD_DLL_SUFFIX = '.dll'
    
    #==================================================================
    # These variables should only be necessary on win32
    
    COPY_CMD = 'copy $SOURCE $TARGET'
    DLLTOOL_CMD = 'dlltool -D $NAME -d $SOURCE -l $TARGET'
    LINK_MSVCR90_FLAGS = '-specs=stub/use-msvcr90.spec'
    MSVCR90_DLL = r'C:\Windows\winsxs\x86_Microsoft.VC90.CRT_1fc8b3b9a1e18e3b_9.0.21022.8_x-ww_d08d0375\msvcr90.dll'
    PEXPORTS_CMD = 'pexports $SOURCE > $TARGET'
    RES_CMD = 'windres --input $SOURCE --output $TARGET --output-format=coff'
    
    # TODO: can we find MINGW_DIR from the environment..?
    MINGW_DIR = r'C:\Program Files\MinGW' 
    MINGW_LIB = os.path.join(MINGW_DIR, 'lib')
    MINGW_INCLUDE = os.path.join(MINGW_DIR, 'include')
    GCCXML_INSERT = '-isystem "%s" -isystem "%s"' % (MINGW_INCLUDE, os.path.join(MINGW_LIB, 'gcc', 'mingw32', '3.4.5', 'include'))


#===============================================================================
# PLATFORM-AGNOSTIC GLOBALS
# If any turn out to need to be platform-specific, please move them

COMPILE_IRONCLAD_FLAGS = '-DIRONCLAD -DPy_BUILD_CORE'
OBJ_CMD = '$CC $CCFLAGS -o $TARGET -c $SOURCE'
DLL_CMD = '$CC $CCFLAGS -shared -o $TARGET $SOURCES'
GCCXML_CMD = ' '.join((GCCXML_CC1PLUS, COMPILE_IRONCLAD_FLAGS, '$INCLUDES -D__GNUC__ %s $SOURCE -fxml="$TARGET"' % GCCXML_INSERT))
PYTHON26OBJ_CMD = OBJ_CMD + ' -I$CPPPATH'
PYTHON26DLL_CMD = DLL_CMD + ' -export-all-symbols'
COMMON = dict(IPY=IPY, IPY_DIR=IPY_DIR)

test_deps = []
before_test = test_deps.append


#===============================================================================
#===============================================================================
# This section builds all the unmanaged parts
# (python26.dll, ic_msvcr90.dll, several test files)
#===============================================================================

native = Environment(tools=NATIVE_TOOLS, ASFLAGS=ASFLAGS, PYTHON_DLL=PYTHON_DLL, **COMMON)
c_obj_kwargs = dict(source_scanner=CScanner(), suffix=OBJ_SUFFIX)
native['BUILDERS']['Obj'] = Builder(action=OBJ_CMD, **c_obj_kwargs)
native['BUILDERS']['Python26Obj'] = Builder(action=PYTHON26OBJ_CMD, CCFLAGS=COMPILE_IRONCLAD_FLAGS, CPPPATH='stub/Include', **c_obj_kwargs)
native['BUILDERS']['Dll'] = Builder(action=DLL_CMD, suffix=DLL_SUFFIX)
native['BUILDERS']['Python26Dll'] = native['BUILDERS']['Dll']
native['BUILDERS']['GccXml'] = Builder(action=GCCXML_CMD, INCLUDES='-Istub/Include', source_scanner=CScanner())

if WIN32:
    # If, RIGHT NOW*, no backup of libmsvcr90.a exists, create one
    # * That is to say: at runtime, not at build time
    
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
    def append_depend(target, source, env):
        return target, source + depend_msvcr90
    native['BUILDERS']['Msvcr90Dll'] = Builder(
        action=DLL_CMD, suffix=DLL_SUFFIX, emitter=append_depend, CCFLAGS=LINK_MSVCR90_FLAGS)
    native['BUILDERS']['Python26Dll'] = Builder(
        action=PYTHON26DLL_CMD, suffix=DLL_SUFFIX, emitter=append_depend, CCFLAGS=LINK_MSVCR90_FLAGS)

#===============================================================================
# Unmanaged libraries for build/ironclad

# Generate data from prebuilt python dll
visible_out = pathmap('data/api', '_visible_api_functions.generated _visible_api_data.generated')
native.Command(visible_out, [],
    '$IPY tools/generateexports.py $PYTHON_DLL data/api')

# Generate stub code
buildstub_names = '_always_register_data_symbols _dont_register_symbols _mgd_function_prototypes _register_data_symbol_priority'
buildstub_src = visible_out + pathmap('data/api', buildstub_names)
buildstub_out = pathmap('stub', 'jumps.generated.asm stubinit.generated.c Include/_mgd_function_prototypes.generated.h')
native.Command(buildstub_out, buildstub_src,
    '$IPY tools/generatestub.py data/api stub')

# Generate information from python headers etc
api_xml = native.GccXml('data/api/_api.generated.xml', 'stub/stubmain.c')

# Compile stub code
jumps_obj = native.Object('stub/jumps.generated.asm')
stubmain_obj = native.Python26Obj('stub/stubmain.c')

# Build and link python26.dll
cpy_src_dirs = 'Modules Objects Parser Python'
cpy_srcs = glommap(lambda x: Glob('stub/%s/*.c' % x), cpy_src_dirs)
cpy_objs = glommap(native.Python26Obj, cpy_srcs)
before_test(native.Python26Dll('build/ironclad/python26', stubmain_obj + jumps_obj + cpy_objs))

if WIN32:
    # This dll redirects various msvcr90 functions so we can DllImport them in C#
    before_test(native.Msvcr90Dll('build/ironclad/ic_msvcr90', native.Obj('stub/ic_msvcr90.c')))

#===============================================================================
# Unmanaged test data

before_test(native.Dll('tests/data/setvalue.pyd', native.Obj('tests/data/src/setvalue.c')))
before_test(native.Dll('tests/data/exportsymbols', native.Obj('tests/data/src/exportsymbols.c')))
before_test(native.Dll('tests/data/fakepython', native.Obj('tests/data/src/fakepython.c')))

if WIN32:
    # Some tests will load and unload dlls which depend on msvcr90; if msvcr90's ref count
    # hits 0 and it gets reloaded, bad things happen. The test framework loads this dll, and
    # keeps it loaded, to prevent aforesaid bad things.
    before_test(native.Msvcr90Dll('tests/data/implicit-load-msvcr90', native.Obj('tests/data/src/empty.c')))

#===============================================================================
#===============================================================================
# This section builds the CLR part
#===============================================================================

managed = Environment(CSC=CSC, **COMMON)
ipy_dlls = 'IronPython IronPython.Modules Microsoft.Dynamic Microsoft.Scripting Microsoft.Scripting.Core'
ipy_refs = ' '.join(submap(IPY_REF_TEMPLATE, ipy_dlls))
managed['BUILDERS']['Dll'] = Builder(action=CSC_CMD, suffix=MGD_DLL_SUFFIX, REFERENCES=ipy_refs)

#===============================================================================
# Generated C#

api_src = api_xml + visible_out + Glob('data/api/*') # TODO: why doesn't Glob pick up items in api_xml, visible_out?
api_out_names = 'Delegates Dispatcher MagicMethods PythonApi PythonStructs'
api_out = pathmap('src', submap('%s.Generated.cs', api_out_names))
managed.Command(api_out, api_src,
    '$IPY tools/generateapiplumbing.py data/api src')

mapper_names = '_exceptions _fill_types _numbers_convert_c2py _numbers_convert_py2c _operator _store_dispatch'
mapper_src = pathmap('data/mapper', mapper_names)
mapper_out = submap('src/PythonMapper%s.Generated.cs', mapper_names)
managed.Command(mapper_out, mapper_src,
    '$IPY tools/generatemapper.py data/mapper src')

snippets_src = Glob('data/snippets/py/*.py')
snippets_out = ['src/CodeSnippets.Generated.cs']
managed.Command(snippets_out, snippets_src,
    '$IPY tools/generatesnippets.py data/snippets/py src')

#===============================================================================
# Build the actual managed library

before_test(managed.Dll('build/ironclad/ironclad', Glob('src/*.cs')))


#===============================================================================
#===============================================================================
# This section runs the tests, assuming you've run 'scons test'
#===============================================================================

tests = Environment(ENV=os.environ, **COMMON)
tests.AlwaysBuild(tests.Alias('test', test_deps,
    '$IPY runtests.py'))
