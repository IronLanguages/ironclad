#===============================================================================
# Various useful functions

import functools
import operator, os, sys
import subprocess
from SCons.Scanner.C import CScanner
# The next import is not necessary, it's just to make linters work
from SCons.Script import ARGUMENTS, Exit, Environment, Builder

def splitstring(f):
    def g(_, s, **kwargs):
        if isinstance(s, str):
            s = s.split()
        return f(_, s, **kwargs)
    return g

@splitstring
def glommap(f, inputs, **kwargs):
    def g(input):
        return f(input, **kwargs)
    return list(functools.reduce(operator.add, map(g, inputs), []))

@splitstring
def pathmap(base, files):
    return list(map(lambda x: os.path.join(base, x), files))

@splitstring
def submap(template, inserts):
    return list(map(lambda x: template % x, inserts))

# To build in debug mode use:
# scons mode=debug
mode = ARGUMENTS.get('mode', 'release')
if not (mode in ['debug', 'release']):
   print("Error: expected 'debug' or 'release', found: " + mode)
   Exit(1)


#===============================================================================
# PLATFORM-SPECIFIC GLOBALS

WIN32 = sys.platform == 'win32'

if WIN32:
    #==================================================================
    # These variables will be needed on any platform, I think

    NATIVE_TOOLS = ['msvc', 'mslink', 'nasm']
    PYD_SUFFIX = '.pyd'

    ASFLAGS = '-f win64'

    # where to find/how to invoke executables
    CASTXML = r'castxml'
    DOTNET = r'dotnet'
    IPY = r'"C:\ironclad\IronPython.3.4.1\net462\ipy.exe"'  # try to use private build
    if not os.path.exists(IPY):
        # use standard location
        IPY = r'"C:\ProgramData\chocolatey\lib\ironpython\ipy.exe"'

    #==================================================================
    # These variables should only be necessary on win32

    MSVCR100_DLL = r'C:\Windows\System32\msvcr100.dll'

    GENDEF_CMD = 'gendef - $SOURCE >$TARGET'
    DLLTOOL_CMD = 'dlltool -D $NAME -d $SOURCE -l $TARGET'
    PEXPORTS_CMD = 'pexports $SOURCE > $TARGET'
    RES_CMD = 'windres --input $SOURCE --output $TARGET --output-format=coff'

    # Find root of CPython installation, used for exports generation and to find DLLs/packages for testing
    # Note: this has to be 64-bit version of CPython 3.4
    CPYTHON34_ROOT = subprocess.check_output(['py.exe', '-3.4-64', '-c', 'import sys, os; print(os.path.dirname(os.path.abspath(sys.executable)))'], universal_newlines=True).strip()
    # If it fails, change to match your installation; by default it is C:\Python34
    #CPYTHON34_ROOT = r'C:\Python34'
    CPYTHON34_DLL = os.path.join(CPYTHON34_ROOT, 'python34.dll')
else:
    NATIVE_TOOLS = ['default', 'clang']
    PYD_SUFFIX = '.so'
    # TODO: linux, darwin


#===============================================================================
# PLATFORM-AGNOSTIC GLOBALS
# If any turn out to need to be platform-specific, please move them

CPYTHON = '"' + sys.executable + '"'  # Python used to run generators from "./tools"

env_with_ippath = os.environ.copy()
env_with_ippath['IRONPYTHONPATH'] = os.getcwd()
env_with_ippath['PYTHONPATH'] = os.getcwd()
# TODO: it should not be necessary to pollute execution with entire os environment

MGD_DLL_SUFFIX = '.dll'
PDB_SUFFIX = '.pdb'

CPPDEFINES = 'Py_ENABLE_SHARED Py_BUILD_CORE IRONCLAD'
CPPPATH = 'stub/Include'
MGD_BUILD_CMD = f'{DOTNET} build --configuration {mode.title()} --nologo --output build/ironclad src/ironclad.csproj'
CASTXML_CMD = f'{CASTXML} "$SOURCE" -o "$TARGET" --castxml-output=1 $CLANGFLAGS $CPPFLAGS $_CPPDEFFLAGS $_CPPINCFLAGS'

# COMMON are globals in all used environments (native, managed, tests, etc.)
COMMON = dict(CPYTHON=CPYTHON, IPY=IPY)

test_deps = []
before_test = test_deps.append


#===============================================================================
#===============================================================================
# This section builds all the unmanaged parts
# (python34.dll and several test files)
#===============================================================================

if WIN32:
    native = Environment(ENV=env_with_ippath, tools=NATIVE_TOOLS, CC='clang-cl', LINK='lld-link',
                         CPYTHON34_DLL=CPYTHON34_DLL, **COMMON)
    native.Append(
        ASFLAGS         = ASFLAGS,
        CPPDEFINES      = f'__MSVCRT_VERSION__=0x1000 _NO_CRT_STDIO_INLINE {CPPDEFINES}',
        CPPPATH         = CPPPATH,
        CLANGFLAGS      = '--target=x86_64-pc-windows-msvc -fuse-ld=lld -fms-compatibility-version=16.00.40219',  # used by clang-cl AND castxml
        CCFLAGS         = '/GS- $CLANGFLAGS',
        LINKFLAGS       = '/subsystem:windows /nodefaultlib:libucrt /nodefaultlib:libcmt',
        SHLINKFLAGS     = '$_DLL_ENTRYPOINT /noimplib',
        no_import_lib   = 1,  # undocumented SCons msvc tools flag; may be renamed in future
        LIBS            = ['kernel32', 'user32'],
        _DLL_ENTRYPOINT = '${"/entry:" + entry if entry else "/noentry"}',
        entry           = '',  # override in SharedLibrary invocation to specify a DLL entry point if needed
    )

    if mode == 'debug':
        native.Replace(PDB='${TARGET.base}' + PDB_SUFFIX)
        native.Append(ASFLAGS='-g')
        native.Append(LINKFLAGS='/debug:full')

    native['BUILDERS']['CastXml'] = Builder(action=CASTXML_CMD, source_scanner=CScanner(), suffix='.xml', CPPDEFPREFIX='-D', INCPREFIX='-I')
else:
    native = Environment(ENV=env_with_ippath, tools=NATIVE_TOOLS,
                         CPYTHON=CPYTHON, CPYTHON34_DLL=CPYTHON34_DLL, **COMMON)
    # TODO: linux, darwin

#===============================================================================
# Unmanaged libraries for build/ironclad

if WIN32:
    # Create implib for msvcrt
    msvcrt_def = native.Command('stub/msvcr100.def', MSVCR100_DLL, GENDEF_CMD)
    msvcrt_lib = native.Command('stub/msvcr100.lib', msvcrt_def, DLLTOOL_CMD, NAME='msvcr100.dll')
else:
    msvcrt_lib = []

# Generate data from prebuilt python dll
exports, python_def = native.Command(['data/api/_exported_functions.generated', 'stub/python34.def'], ['tools/generateexports.py'],
    '$CPYTHON tools/generateexports.py $CPYTHON34_DLL data/api stub')

# Generate stub code
buildstub_names = '_extra_functions _mgd_api_data _pure_c_symbols'
buildstub_src = [exports] + pathmap('data/api', buildstub_names)
buildstub_out = pathmap('stub', 'jumps.generated.asm stubinit.generated.c Include/_extra_functions.generated.h')
native.Command(buildstub_out, buildstub_src + ['tools/generatestub.py'],
    '$CPYTHON tools/generatestub.py data/api stub')

# Compile stub code
# SharedObject builder does not support assembly code
# since whether the code is position-independent (shareable) or not depends on assembly instructions used, not assembler flags
jumps_obj = native.Object('stub/jumps.generated.asm')
stubmain_obj = native.SharedObject('stub/stubmain.c')

# Generate information from python headers etc
stubmain_xml = native.CastXml('data/api/_stubmain.generated.xml', 'stub/stubmain.c')

# Build and link python34.dll
cpy_src_dirs = 'Modules Objects Parser Python'
cpy_srcs = glommap(lambda x: native.Glob('stub/%s/*.c' % x), cpy_src_dirs)
cpy_objs = glommap(native.SharedObject, cpy_srcs)
before_test(native.SharedLibrary('build/ironclad/python34', [cpy_objs, jumps_obj, stubmain_obj, msvcrt_lib, python_def], entry='DllMain'))

#===============================================================================
# Unmanaged test data

before_test(native.SharedLibrary('tests/data/setvalue', 'tests/data/src/setvalue.c', SHLIBSUFFIX=PYD_SUFFIX))
before_test(native.SharedLibrary('tests/data/exportsymbols', 'tests/data/src/exportsymbols.c'))
before_test(native.SharedLibrary('tests/data/fakepython', 'tests/data/src/fakepython.c',))

if WIN32:
    # Some tests will load and unload dlls which depend on msvcr100; if msvcr100's ref count
    # hits 0 and it gets reloaded, bad things happen. The test framework loads this dll, and
    # keeps it loaded, to prevent aforesaid bad things.
    before_test(native.SharedLibrary('tests/data/implicit-load-msvcr100', 'tests/data/src/empty.c'))

#===============================================================================
#===============================================================================
# This section builds the CLR part
#===============================================================================

managed = Environment(ENV=env_with_ippath, **COMMON)

def dotnet_emitter(target, source, env):
    return [[t, str(t).removesuffix(MGD_DLL_SUFFIX) + PDB_SUFFIX] for t in target], source
managed['BUILDERS']['Dll'] = Builder(action=MGD_BUILD_CMD, suffix=MGD_DLL_SUFFIX, emitter=dotnet_emitter)

#===============================================================================
# Generated C#

api_src = managed.Glob('data/api/*')
# Glob runs before the build so during a clean build it won't pick up generated files
api_src += [stubmain_xml, exports]
api_out_names = 'Delegates Dispatcher MagicMethods PythonApi PythonStructs'
api_out = pathmap('src', submap('%s.Generated.cs', api_out_names))
managed.Command(api_out, api_src + ['tools/generateapiplumbing.py'],
    '$CPYTHON tools/generateapiplumbing.py data/api src')

mapper_names = [name for name in os.listdir('data/mapper') if name.startswith('_')]
mapper_src = pathmap('data/mapper', mapper_names)
mapper_out = submap('src/mapper/PythonMapper%s.Generated.cs', mapper_names)
managed.Command(mapper_out, mapper_src + ['tools/generatemapper.py'],
    '$CPYTHON tools/generatemapper.py data/mapper src/mapper')

snippets_src = managed.Glob('data/snippets/py/*.py')
snippets_out = ['src/CodeSnippets.Generated.cs']
managed.Command(snippets_out, snippets_src + ['tools/generatecodesnippets.py'],
    '$CPYTHON tools/generatecodesnippets.py data/snippets/py src')

#===============================================================================
# Build the actual managed library

ironclad_dll_src = list(map(managed.Glob, ('src/*.cs', 'src/mapper/*.cs')))
before_test(managed.Dll('build/ironclad/ironclad', ironclad_dll_src))


#===============================================================================
#===============================================================================
# This section installs the package initialization module (__init__.py)
#===============================================================================

pkginit = Environment(tools=['filesystem'], **COMMON)
before_test(pkginit.CopyAs('build/ironclad/__init__.py', 'data/ironclad__init__.py'))


#===============================================================================
#===============================================================================
# This section runs the tests, assuming you've run 'scons test'
#===============================================================================

tests = Environment(ENV=os.environ.copy(), **COMMON)
tests['ENV']['IRONPYTHONPATH'] = "."
tests.AppendENVPath('IRONPYTHONPATH', os.path.join(CPYTHON34_ROOT, "DLLs"))  # required to import/access dlls
tests.AppendENVPath('IRONPYTHONPATH', os.path.join(CPYTHON34_ROOT, "Lib/site-packages"))  # pysvn test
tests.AlwaysBuild(tests.Alias('test', test_deps,
    '$IPY runtests.py'))
