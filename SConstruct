#===============================================================================
# Various useful functions

import functools
import operator, os, sys
import subprocess
from SCons.Scanner.C import CScanner
# The next import is not necessary, it's just to make linters work
from SCons.Script import ARGUMENTS, Exit, Environment, Builder

def splitstring(f):
    def g(_, s):
        if isinstance(s, str):
            s = s.split()
        return f(_, s)
    return g

@splitstring
def glommap(f, inputs):
    return list(functools.reduce(operator.add, map(f, inputs), []))

@splitstring
def pathmap(base, files):
    return list(map(lambda x: os.path.join(base, x), files))

@splitstring
def submap(template, inserts):
    return list(map(lambda x: template % x, inserts))

# to build in debug mode (for now c# only) use:
# scons mode=debug
mode = ARGUMENTS.get('mode', 'release')
if not (mode in ['debug', 'release']):
   print("Error: expected 'debug' or 'release', found: " + mode)
   Exit(1)


#===============================================================================
# PLATFORM-SPECIFIC GLOBALS

WIN32 = sys.platform == 'win32'

CPYTHON = '"' + sys.executable + '"'  # Python used to run generators from "./tools"

if WIN32:
    #==================================================================
    # These variables will be needed on any platform, I think
    
    ASFLAGS = '-f win64'
    CSC = r'C:\windows\Microsoft.NET\Framework\v4.0.30319\csc.exe'
    CSC_CMD = 'dotnet build '
    if mode == 'debug':
        CSC_CMD += '--configuration Debug '
    else:
        CSC_CMD += '--configuration Release '
    CSC_CMD += '--nologo --output build/ironclad src/Ironclad.csproj'
    CASTXML = r'castxml'

    # private build
    IPY = r'"C:\ironclad\IronPython.3.4.1\net462\ipy.exe"'
    if not os.path.exists(IPY):
        # standard location
        IPY = r'"C:\ProgramData\chocolatey\lib\ironpython\ipy.exe"'

    NATIVE_TOOLS = ['mingw', 'nasm']
    
    OBJ_SUFFIX = '.o'
    DLL_SUFFIX = '.dll'
    MGD_DLL_SUFFIX = '.dll'
    
    #==================================================================
    # These variables should only be necessary on win32
    
    DLLTOOL_CMD = 'dlltool -D $NAME -d $SOURCE -l $TARGET'
    LINK_MSVCR100_FLAGS = '-specs=stub/use-msvcr100.spec'
    PEXPORTS_CMD = 'pexports $SOURCE > $TARGET'
    RES_CMD = 'windres --input $SOURCE --output $TARGET --output-format=coff'
    
    # TODO: can we find MINGW_DIR from the environment..?
    MINGW_DIR = r'C:\mingw64'
    MINGW_LIB = os.path.join(MINGW_DIR, 'lib')
    MINGW_INCLUDE = os.path.join(MINGW_DIR, 'include')
    GCCXML_INSERT = ''

    # Find root of CPython installation, used for exports generation and to find DLLs/packages for testing
    # Note: this has to be 64-bit version of CPython 3.4
    CPYTHON34_ROOT = subprocess.check_output(['py.exe', '-3.4-64', '-c', 'import sys, os; print(os.path.dirname(os.path.abspath(sys.executable)))'], universal_newlines=True).strip()
    # If it fails, change to match your installation; by default it is C:\Python34
    #CPYTHON34_ROOT = r'C:\Python34'
    CPYTHON34_DLL = os.path.join(CPYTHON34_ROOT, 'python34.dll')


#===============================================================================
# PLATFORM-AGNOSTIC GLOBALS
# If any turn out to need to be platform-specific, please move them
env_with_ippath = os.environ.copy()
env_with_ippath['IRONPYTHONPATH'] = os.getcwd()
env_with_ippath['PYTHONPATH'] = os.getcwd()
# TODO: it should not be necessary to pollute execution with entire os environment

COMPILE_IRONCLAD_FLAGS = '-DIRONCLAD -DPy_BUILD_CORE -D__MSVCRT_VERSION__=0x1000 -DMS_WIN64'
OBJ_CMD = '$CC -m64 -fcommon $CCFLAGS -o $TARGET -c $SOURCE' # TODO: get rid of -fcommon
DLL_CMD = '$CC -m64 $CCFLAGS -shared -o $TARGET $SOURCES'
GCCXML_CMD = ' '.join((CASTXML, COMPILE_IRONCLAD_FLAGS, '-v -I$CPPPATH -D__GNUC__ %s $SOURCE -o "$TARGET" --castxml-output=1' % GCCXML_INSERT))
PYTHON34OBJ_CMD = OBJ_CMD + ' -I$CPPPATH'
PYTHON34DLL_CMD = DLL_CMD + ' -Xlinker --export-all-symbols'
COMMON = dict(IPY=IPY)

test_deps = []
before_test = test_deps.append


#===============================================================================
#===============================================================================
# This section builds all the unmanaged parts
# (python34.dll, ic_msvcr90.dll, several test files)
#===============================================================================

native = Environment(ENV=env_with_ippath, tools=NATIVE_TOOLS, ASFLAGS=ASFLAGS, CPYTHON=CPYTHON, CPYTHON34_DLL=CPYTHON34_DLL, **COMMON)
c_obj_kwargs = dict(source_scanner=CScanner(), suffix=OBJ_SUFFIX)
native['BUILDERS']['Obj'] = Builder(action=OBJ_CMD, **c_obj_kwargs)
native['BUILDERS']['Python34Obj'] = Builder(action=PYTHON34OBJ_CMD, CCFLAGS=COMPILE_IRONCLAD_FLAGS, CPPPATH='stub/Include', **c_obj_kwargs)
native['BUILDERS']['Dll'] = Builder(action=DLL_CMD, suffix=DLL_SUFFIX)
native['BUILDERS']['Python34Dll'] = native['BUILDERS']['Dll']
native['BUILDERS']['GccXml'] = Builder(action=GCCXML_CMD, CPPPATH='stub/Include', source_scanner=CScanner())

if WIN32:
    # These builders should ensure that their targets correctly link with msvcr100.dll
    def append_depend(target, source, env):
        return target, source
    native['BUILDERS']['Msvcr100Dll'] = Builder(
        action=DLL_CMD, suffix=DLL_SUFFIX, emitter=append_depend, CCFLAGS=LINK_MSVCR100_FLAGS)
    native['BUILDERS']['Python34Dll'] = Builder(
        action=PYTHON34DLL_CMD, suffix=DLL_SUFFIX, emitter=append_depend, CCFLAGS=LINK_MSVCR100_FLAGS)

#===============================================================================
# Unmanaged libraries for build/ironclad

# Generate data from prebuilt python dll
exports = native.Command('data/api/_exported_functions.generated', [],
    '$CPYTHON tools/generateexports.py $CPYTHON34_DLL data/api')

# Generate stub code
buildstub_names = '_extra_functions _mgd_api_data _pure_c_symbols'
buildstub_src = exports + pathmap('data/api', buildstub_names)
buildstub_out = pathmap('stub', 'jumps.generated.asm stubinit.generated.c Include/_extra_functions.generated.h')
native.Command(buildstub_out, buildstub_src,
    '$CPYTHON tools/generatestub.py data/api stub')

# Compile stub code
jumps_obj = native.Object('stub/jumps.generated.asm')
stubmain_obj = native.Python34Obj('stub/stubmain.c')

# Generate information from python headers etc
stubmain_xml = native.GccXml('data/api/_stubmain.generated.xml', 'stub/stubmain.c')

# Build and link python34.dll
cpy_src_dirs = 'Modules Objects Parser Python'
cpy_srcs = glommap(lambda x: native.Glob('stub/%s/*.c' % x), cpy_src_dirs)
cpy_objs = glommap(native.Python34Obj, cpy_srcs)
before_test(native.Python34Dll('build/ironclad/python34', stubmain_obj + jumps_obj + cpy_objs))

if WIN32:
    # This dll redirects various msvcr90 functions so we can DllImport them in C#
    #pass
    before_test(native.Msvcr100Dll('build/ironclad/ic_msvcr90', native.Obj('stub/ic_msvcr90.c')))

#===============================================================================
# Unmanaged test data

before_test(native.Dll('tests/data/setvalue.pyd', native.Obj('tests/data/src/setvalue.c')))
before_test(native.Dll('tests/data/exportsymbols', native.Obj('tests/data/src/exportsymbols.c')))
before_test(native.Dll('tests/data/fakepython', native.Obj('tests/data/src/fakepython.c')))

if WIN32:
    # Some tests will load and unload dlls which depend on msvcr90; if msvcr90's ref count
    # hits 0 and it gets reloaded, bad things happen. The test framework loads this dll, and
    # keeps it loaded, to prevent aforesaid bad things.
    before_test(native.Msvcr100Dll('tests/data/implicit-load-msvcr90', native.Obj('tests/data/src/empty.c')))

#===============================================================================
#===============================================================================
# This section builds the CLR part
#===============================================================================
managed = Environment(ENV=env_with_ippath, CSC=CSC, CPYTHON=CPYTHON, **COMMON)
managed['BUILDERS']['Dll'] = Builder(action=CSC_CMD, suffix=MGD_DLL_SUFFIX)

#===============================================================================
# Generated C#

api_src = managed.Glob('data/api/*')
# Glob runs before the build so during a clean build it won't pick up generated files
api_src += stubmain_xml + exports
api_out_names = 'Delegates Dispatcher MagicMethods PythonApi PythonStructs'
api_out = pathmap('src', submap('%s.Generated.cs', api_out_names))
managed.Command(api_out, api_src,
    '$CPYTHON tools/generateapiplumbing.py data/api src')

mapper_names = [name for name in os.listdir('data/mapper') if name.startswith('_')]
mapper_src = pathmap('data/mapper', mapper_names)
mapper_out = submap('src/mapper/PythonMapper%s.Generated.cs', mapper_names)
managed.Command(mapper_out, mapper_src,
    '$CPYTHON tools/generatemapper.py data/mapper src/mapper')

snippets_src = managed.Glob('data/snippets/py/*.py')
snippets_out = ['src/CodeSnippets.Generated.cs']
managed.Command(snippets_out, snippets_src,
    '$CPYTHON tools/generatecodesnippets.py data/snippets/py src')

#===============================================================================
# Build the actual managed library

ironclad_dll_src = list(map(managed.Glob, ('src/*.cs', 'src/mapper/*.cs')))
before_test(managed.Dll('build/ironclad/ironclad', ironclad_dll_src))

#===============================================================================
#===============================================================================
# This section runs the tests, assuming you've run 'scons test'
#===============================================================================

testenv = os.environ
testenv['IRONPYTHONPATH'] = "."
testenv['IRONPYTHONPATH'] += ";" + os.path.join(CPYTHON34_ROOT, "DLLs") # required to import/access dlls
testenv['IRONPYTHONPATH'] += ";" + os.path.join(CPYTHON34_ROOT, "Lib/site-packages") # pysvn test
tests = Environment(ENV=testenv, **COMMON)
tests.AlwaysBuild(tests.Alias('test', test_deps,
    '$IPY runtests.py'))
