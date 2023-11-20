# Main Ironclad build script
#
# Builds one configuration/framework/platform combination.
# By default the build is in-source (intermediate build artifacts are placed next to source files).
# The build output is placed in directory 'build'.
# Recognizes one command-line build variable 'mode'
# which can have values 'release' (default) or 'debug'
# To build in-source in debug mode use:
# scons mode=debug


#===============================================================================
# Various useful functions

import functools
import operator, os, sys
import subprocess
from SCons.Scanner.C import CScanner

EnsurePythonVersion(3, 9)

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


#===============================================================================
# BUILD CONFIGURATION

mode = ARGUMENTS.get('mode', 'release')
if not (mode in ['debug', 'release']):
   print("Error: expected 'debug' or 'release', found: " + mode)
   Exit(1)

PROJECT_DIR = Dir('#').abspath              # project root, where all commands are run
BUILD_DIR = Dir('#').rel_path(Dir('.'))     # for intermediate build artifacts (in-source by default)
OUT_DIR = 'build'                           # for build output (final) artifacts (default location)
Import('*')                                 # can override aby of the variables above


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

OS_ENV = os.environ.copy()
OS_ENV['IRONPYTHONPATH'] = PROJECT_DIR
OS_ENV['PYTHONPATH'] = PROJECT_DIR
# TODO: it should not be necessary to pollute execution with entire os environment

MGD_DLL_SUFFIX = '.dll'
PDB_SUFFIX = '.pdb'

CPPDEFINES = 'Py_ENABLE_SHARED Py_BUILD_CORE IRONCLAD'
CPPPATH = 'stub/Include'
DOTNET_CMD = f'{DOTNET} %(cmd)s --configuration {mode.title()} --nologo --output ${{TARGET.dir}} $SOURCE'
MGD_BUILD_CMD = DOTNET_CMD % {'cmd' : 'build'}
MGD_CLEAN_CMD = DOTNET_CMD % {'cmd' : 'clean'}
CASTXML_CMD = f'{CASTXML} "$SOURCE" -o "$TARGET" --castxml-output=1 $CLANGFLAGS $CPPFLAGS $_CPPDEFFLAGS $_CPPINCFLAGS'

# COMMON are globals in all used environments (native, managed, tests, etc.)
COMMON = dict(CPYTHON=CPYTHON, IPY=IPY, BUILD_DIR=BUILD_DIR, OUT_DIR=OUT_DIR, PROJECT_DIR=PROJECT_DIR)

test_deps = []
before_test = test_deps.append


#===============================================================================
#===============================================================================
# This section builds all the unmanaged parts
# (python34.dll and several test files)
#===============================================================================

if WIN32:
    native = Environment(ENV=OS_ENV, tools=NATIVE_TOOLS, CC='clang-cl', LINK='lld-link',
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
    native = Environment(ENV=OS_ENV, tools=NATIVE_TOOLS,
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
exports, python_def = native.Command(['data/api/_exported_functions.generated', 'stub/python34.def'], [],
    '$CPYTHON tools/generateexports.py $CPYTHON34_DLL $BUILD_DIR/data/api $BUILD_DIR/stub')
native.Depends([exports, python_def], '#tools/generateexports.py')

# Generate stub code
buildstub_names = '_extra_functions _mgd_api_data _pure_c_symbols'
buildstub_src = [exports] + pathmap('data/api', buildstub_names)
buildstub_out = pathmap('stub', 'jumps.generated.asm stubinit.generated.c Include/_extra_functions.generated.h')
native.Command(buildstub_out, buildstub_src,
    '$CPYTHON tools/generatestub.py $BUILD_DIR/data/api $BUILD_DIR/stub')
native.Depends(buildstub_out, '#tools/generatestub.py')

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
before_test(native.SharedLibrary('#$OUT_DIR/ironclad/python34', [cpy_objs, jumps_obj, stubmain_obj, msvcrt_lib, python_def], entry='DllMain'))

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

managed = Environment(ENV=OS_ENV, **COMMON)

def dotnet_emitter(target, source, env):
    return [[t, str(t).removesuffix(MGD_DLL_SUFFIX) + PDB_SUFFIX] for t in target], source
managed['BUILDERS']['Dll'] = Builder(action=MGD_BUILD_CMD, suffix=MGD_DLL_SUFFIX, emitter=dotnet_emitter)

#===============================================================================
# Generated C#

api_src = managed.Glob('data/api/*')
api_out_names = 'Delegates Dispatcher MagicMethods PythonApi PythonStructs'
api_out = pathmap('src', submap('%s.Generated.cs', api_out_names))
managed.Command(api_out, api_src,
    '$CPYTHON tools/generateapiplumbing.py $BUILD_DIR/data/api $BUILD_DIR/src')
managed.Depends(api_out, '#tools/generateapiplumbing.py')

mapper_src = managed.Glob('data/mapper/_*')
mapper_out = submap('src/mapper/PythonMapper%s.Generated.cs', map(lambda x: x.name, mapper_src))
managed.Command(mapper_out, mapper_src,
    '$CPYTHON tools/generatemapper.py $BUILD_DIR/data/mapper $BUILD_DIR/src/mapper')
managed.Depends(mapper_out, '#tools/generatemapper.py')

snippets_src = managed.Glob('data/snippets/py/*.py')
snippets_out = ['src/CodeSnippets.Generated.cs']
managed.Command(snippets_out, snippets_src,
    '$CPYTHON tools/generatecodesnippets.py $BUILD_DIR/data/snippets/py $BUILD_DIR/src')
managed.Depends(snippets_out, '#tools/generatecodesnippets.py')

#===============================================================================
# Build the actual managed library

ironclad_dll_src = list(map(managed.Glob, ('src/*.cs', 'src/mapper/*.cs')))
ironclad_dll = managed.Dll('#$OUT_DIR/ironclad/ironclad', 'src/ironclad.csproj')
managed.Depends(ironclad_dll, ironclad_dll_src)
before_test(ironclad_dll)

if managed.GetOption('clean'):
    # 'Execute' runs while reading the SCons script (before actual build)
    # and in the variant dir (BUILD_DIR)
    managed.Execute(managed.subst(MGD_CLEAN_CMD,
                                  target=File('$PROJECT_DIR/$OUT_DIR/ironclad/ironclad'),
                                  source=File('src/ironclad.csproj')))


#===============================================================================
#===============================================================================
# This section installs the package initialization module (__init__.py)
#===============================================================================

pkginit = Environment(tools=['filesystem'], **COMMON)
before_test(pkginit.CopyAs('#$OUT_DIR/ironclad/__init__.py', 'data/ironclad__init__.py'))


#===============================================================================
#===============================================================================
# This section runs the tests, assuming you've run 'scons test'
#===============================================================================

tests = Environment(ENV=OS_ENV, **COMMON)
tests['ENV']['TESTDATA_BUILDDIR'] = os.path.join(BUILD_DIR, "tests", "data")
tests.PrependENVPath('IRONPYTHONPATH', OUT_DIR)  # to find ironclad
tests.AppendENVPath('IRONPYTHONPATH', os.path.join(CPYTHON34_ROOT, "DLLs"))  # required to import/access dlls
tests.AppendENVPath('IRONPYTHONPATH', os.path.join(CPYTHON34_ROOT, "Lib", "site-packages"))  # pysvn test

tests.AlwaysBuild(tests.Alias('test', test_deps,
    '$IPY runtests.py'))
