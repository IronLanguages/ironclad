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

# to build in debug mode (for now c# only) use:
# scons mode=debug
mode = ARGUMENTS.get('mode', 'release')
if not (mode in ['debug', 'release']):
   print "Error: expected 'debug' or 'release', found: " + mode
   Exit(1)


#===============================================================================
# PLATFORM-SPECIFIC GLOBALS

WIN32 = sys.platform == 'win32'

if WIN32:
    #==================================================================
    # These variables will be needed on any platform, I think
    
    ASFLAGS = '-f win32'
    CSC = r'C:\windows\Microsoft.NET\Framework\v4.0.30319\csc.exe'
    CSC_CMD = '$CSC '
    if mode == 'debug':
        CSC_CMD += '/debug '
    CSC_CMD += '/nologo /out:$TARGET /t:library $REFERENCES $SOURCES'
    GCCXML_CC1PLUS = r'"C:\Program Files (x86)\gccxml\bin\gccxml_cc1plus.exe"'

    # standard location
    IPY = r'"C:\Program Files (x86)\IronPython 2.7\ipy.exe"'
    IPY_DIR = r'"C:\Program Files (x86)\IronPython 2.7"'
    # private build
    # IPY = r'"C:\github\IronLanguages\bin\Debug\ipy.exe"'
    # IPY_DIR = r'"C:\github\IronLanguages\bin\Debug"'

    IPY_REF_TEMPLATE = r'/r:$IPY_DIR\%s.dll'
    NATIVE_TOOLS = ['mingw', 'nasm']
    PYTHON_DLL = r'C:\windows\SysWOW64\python27.dll'
    
    OBJ_SUFFIX = '.o'
    DLL_SUFFIX = '.dll'
    MGD_DLL_SUFFIX = '.dll'
    
    #==================================================================
    # These variables should only be necessary on win32
    
    COPY_CMD = 'copy $SOURCE $TARGET'
    DLLTOOL_CMD = 'dlltool -D $NAME -d $SOURCE -l $TARGET'
    LINK_MSVCR90_FLAGS = '-specs=stub/use-msvcr90.spec'
    MSVCR90_DLL = r'C:\Windows\winsxs\x86_microsoft.vc90.crt_1fc8b3b9a1e18e3b_9.0.30729.6161_none_50934f2ebcb7eb57\msvcr90.dll'
    PEXPORTS_CMD = 'pexports $SOURCE > $TARGET'
    RES_CMD = 'windres --input $SOURCE --output $TARGET --output-format=coff'
    
    # TODO: can we find MINGW_DIR from the environment..?
    MINGW_DIR = r'C:\MinGW'
    MINGW_LIB = os.path.join(MINGW_DIR, 'lib')
    MINGW_INCLUDE = os.path.join(MINGW_DIR, 'include')
    GCCXML_INSERT = '-isystem "%s" -isystem "%s"' % (MINGW_INCLUDE, os.path.join(MINGW_LIB, 'gcc', 'mingw32', '4.8.1', 'include'))

    # Calculate DLLs dir of cpython - assume this is run from the cpython
    # If not, change to match your instalation, defaults to C:\Python27\DLLs
    # Note: this has to be 32bit version of cpython
    CPYTHON_DLLS = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "DLLs")


#===============================================================================
# PLATFORM-AGNOSTIC GLOBALS
# If any turn out to need to be platform-specific, please move them
env_with_ippath = os.environ
env_with_ippath['IRONPYTHONPATH'] = os.getcwd()
# TODO: it should not be necessary to polute execution with entire os environment

COMPILE_IRONCLAD_FLAGS = '-DIRONCLAD -DPy_BUILD_CORE'
OBJ_CMD = '$CC $CCFLAGS -o $TARGET -c $SOURCE'
DLL_CMD = '$CC $CCFLAGS -shared -o $TARGET $SOURCES'
GCCXML_CMD = ' '.join((GCCXML_CC1PLUS, COMPILE_IRONCLAD_FLAGS, '-I$CPPPATH -D__GNUC__ %s $SOURCE -fxml="$TARGET"' % GCCXML_INSERT))
PYTHON27OBJ_CMD = OBJ_CMD + ' -I$CPPPATH'
PYTHON27DLL_CMD = DLL_CMD + ' -Xlinker --export-all-symbols'
COMMON = dict(IPY=IPY, IPY_DIR=IPY_DIR)

test_deps = []
before_test = test_deps.append


#===============================================================================
#===============================================================================
# This section builds all the unmanaged parts
# (python27.dll, ic_msvcr90.dll, several test files)
#===============================================================================

native = Environment(ENV=env_with_ippath, tools=NATIVE_TOOLS, ASFLAGS=ASFLAGS, PYTHON_DLL=PYTHON_DLL, **COMMON)
c_obj_kwargs = dict(source_scanner=CScanner(), suffix=OBJ_SUFFIX)
native['BUILDERS']['Obj'] = Builder(action=OBJ_CMD, **c_obj_kwargs)
native['BUILDERS']['Python27Obj'] = Builder(action=PYTHON27OBJ_CMD, CCFLAGS=COMPILE_IRONCLAD_FLAGS, CPPPATH='stub/Include', **c_obj_kwargs)
native['BUILDERS']['Dll'] = Builder(action=DLL_CMD, suffix=DLL_SUFFIX)
native['BUILDERS']['Python27Dll'] = native['BUILDERS']['Dll']
native['BUILDERS']['GccXml'] = Builder(action=GCCXML_CMD, CPPPATH='stub/Include', source_scanner=CScanner())

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
    native['BUILDERS']['Python27Dll'] = Builder(
        action=PYTHON27DLL_CMD, suffix=DLL_SUFFIX, emitter=append_depend, CCFLAGS=LINK_MSVCR90_FLAGS)

#===============================================================================
# Unmanaged libraries for build/ironclad

# Generate data from prebuilt python dll
exports = native.Command('data/api/_exported_functions.generated', [],
    '$IPY tools/generateexports.py $PYTHON_DLL data/api')

# Generate stub code
buildstub_names = '_extra_functions _mgd_api_data _pure_c_symbols'
buildstub_src = exports + pathmap('data/api', buildstub_names)
buildstub_out = pathmap('stub', 'jumps.generated.asm stubinit.generated.c Include/_extra_functions.generated.h')
native.Command(buildstub_out, buildstub_src,
    '$IPY tools/generatestub.py data/api stub')

# Compile stub code
jumps_obj = native.Object('stub/jumps.generated.asm')
stubmain_obj = native.Python27Obj('stub/stubmain.c')

# Generate information from python headers etc
stubmain_xml = native.GccXml('data/api/_stubmain.generated.xml', 'stub/stubmain.c')

# Build and link python27.dll
cpy_src_dirs = 'Modules Objects Parser Python'
cpy_srcs = glommap(lambda x: native.Glob('stub/%s/*.c' % x), cpy_src_dirs)
cpy_objs = glommap(native.Python27Obj, cpy_srcs)
before_test(native.Python27Dll('build/ironclad/python27', stubmain_obj + jumps_obj + cpy_objs))

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
managed = Environment(ENV=env_with_ippath, CSC=CSC, **COMMON)
ipy_dlls = 'IronPython IronPython.Modules Microsoft.Dynamic Microsoft.Scripting Microsoft.Scripting.Metadata'
ipy_refs = ' '.join(submap(IPY_REF_TEMPLATE, ipy_dlls))
numeric_ref = r'/r:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.0\System.Numerics.dll"'
managed['BUILDERS']['Dll'] = Builder(action=CSC_CMD, suffix=MGD_DLL_SUFFIX, REFERENCES=ipy_refs + ' ' + numeric_ref)

#===============================================================================
# Generated C#

api_src = stubmain_xml + exports + managed.Glob('data/api/*') # TODO: why doesn't Glob pick up items in stubmain_xml, exports?
api_out_names = 'Delegates Dispatcher MagicMethods PythonApi PythonStructs'
api_out = pathmap('src', submap('%s.Generated.cs', api_out_names))
managed.Command(api_out, api_src,
    '$IPY tools/generateapiplumbing.py data/api src')

mapper_names = [name for name in os.listdir('data/mapper') if name.startswith('_')]
mapper_src = pathmap('data/mapper', mapper_names)
mapper_out = submap('src/mapper/PythonMapper%s.Generated.cs', mapper_names)
managed.Command(mapper_out, mapper_src,
    '$IPY tools/generatemapper.py data/mapper src/mapper')

snippets_src = managed.Glob('data/snippets/py/*.py')
snippets_out = ['src/CodeSnippets.Generated.cs']
managed.Command(snippets_out, snippets_src,
    '$IPY tools/generatecodesnippets.py data/snippets/py src')

#===============================================================================
# Build the actual managed library

ironclad_dll_src = map(managed.Glob, ('src/*.cs', 'src/mapper/*.cs'))
before_test(managed.Dll('build/ironclad/ironclad', ironclad_dll_src))

#===============================================================================
#===============================================================================
# This section runs the tests, assuming you've run 'scons test'
#===============================================================================

testenv = os.environ
testenv['IRONPYTHONPATH'] = CPYTHON_DLLS
tests = Environment(ENV=testenv, **COMMON)
tests.AlwaysBuild(tests.Alias('test', test_deps,
    '$IPY runtests.py'))
