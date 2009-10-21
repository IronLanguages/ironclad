

#===============================================================================
# useful
import operator, os
opj = os.path.join

def glommap(f, iter):
    'agglomerates lists returned from map(f, iter)'
    return reduce(operator.add, map(f, iter), [])

def pathmap(base, files):
    'prepend common path to file list'
    if isinstance(files, basestring):
        files = files.split()
    return map(lambda x: opj(base, x), files)

COMMON = dict(
    IPY='"C:\\Program Files\\IronPython 2.6\\ipy.exe"',
    IPY_DIR='"C:\\Program Files\\IronPython 2.6"')


#===============================================================================
#===============================================================================
# This section builds the CLR bits
#===============================================================================
managed = Environment(
    CSC='C:\\windows\\Microsoft.NET\\Framework\\v2.0.50727\\csc.exe',
    **COMMON)

ipy_dlls = 'IronPython IronPython.Modules Microsoft.Dynamic Microsoft.Scripting Microsoft.Scripting.Core'
ipy_refs = ' '.join(map(lambda x: '/r:$IPY_DIR\\%s.dll' % x, ipy_dlls.split()))
managed['BUILDERS']['Dll'] = Builder(action='$CSC /nologo /out:$TARGET /t:library %s $SOURCES' % ipy_refs)
managed['BUILDERS']['Insert'] = Builder(action='$IPY tools/insertfiles.py $SOURCES > $TARGET')

#===============================================================================
# generated code: note whole heaps of ugly implicit dependencies

generated = []
dispatcher_sources = pathmap('tools',
    'dispatcherinputs.py dispatchersnippets.py generatedispatcher.py platform.py '
    '_mgd_api_functions _mgd_api_functions _all_api_functions')
dispatcher_sources += pathmap('stub', '_mgd_functions _ignore_symbols')
dispatcher_outputs = pathmap('src', 'Delegates Dispatcher MagicMethods Python25Api')
generated.extend(managed.Command(dispatcher_outputs, dispatcher_sources, '$IPY tools/generatedispatcher.py src'))

mapper_basenames = 'exceptions fill_types numbers_convert_c2py numbers_convert_py2c operator store_dispatch'.split()
mapper_sources = pathmap('src/python25mapper_components', mapper_basenames)
mapper_outputs = pathmap('src', map((lambda x: 'Python25Mapper_%s.Generated.cs' % x), mapper_basenames))
generated.extend(managed.Command(mapper_outputs, mapper_sources, '$IPY tools/generatepython25mapper.py src/python25mapper_components src'))

# CodeSnippets_kindaDictProxy.Generated.cs
components_dir = 'src/python25mapper_components'
codesnippet_in = lambda x, y: pathmap(components_dir, [('CodeSnippets_%s.cs.src' % x), ('%s.py' % y)])
codesnippet_out = lambda x: 'src/CodeSnippets_%s.Generated.cs' % x
generated.extend(managed.Insert(codesnippet_out('ihooks'), codesnippet_in('ihooks', 'import_code')))
generated.extend(managed.Insert(codesnippet_out('kindaDictProxy'), codesnippet_in('kindaDictProxy', 'kindadictproxy')))
generated.extend(managed.Insert(codesnippet_out('kindaSeqIter'), codesnippet_in('kindaSeqIter', 'kindaseqiter')))

managed.Dll('build/ironclad/ironclad.dll', Glob('src/*.cs'))


#===============================================================================
#===============================================================================
# This section builds all the unmanaged stuff
# (python26.dll, ic_msvcr90.dll, test data)
#===============================================================================
native = Environment(
    tools=['mingw', 'nasm'], 
    ASFLAGS='-f win32', 
    CCFLAGS='-specs=stub/use-msvcr90.spec -DIRONCLAD -DPy_BUILD_CORE',
    CPPPATH='stub/Include',
    PYTHON_DLL='"C:\\windows\\system32\\python26.dll"',
    **COMMON)

native['BUILDERS']['Obj'] = Builder(action='$CC $CCFLAGS -o $TARGET -c $SOURCE -I $CPPPATH')
native['BUILDERS']['Dll'] = Builder(action='$CC $CCFLAGS -export-all-symbols -shared -o $TARGET $SOURCES')
native['BUILDERS']['Res'] = Builder(action='windres --input $SOURCE --output $TARGET --output-format=coff')

# This resource needs to be embedded in several C libraries, so winsxs doesn't get huffy at runtime
depend_msvcr90 = native.Res('stub/depend-msvcr90.res', 'stub/depend-msvcr90.rc')
native.Depends(depend_msvcr90, 'stub/depend-msvcr90.manifest')

#===============================================================================
# contents of build/ironclad

# this dll redirects various msvcr90 functions so we can DllImport them
native.Dll('build/ironclad/ic_msvcr90.dll', native.Obj('stub/ic_msvcr90.c') + depend_msvcr90)

# generate stub code
buildstub_sources = pathmap('stub', '_ordered_data _mgd_functions _ignore_symbols _extra_data')
buildstub_outputs = pathmap('stub', 'jumps.generated.asm stubinit.generated.c')
native.Command(buildstub_outputs, buildstub_sources, '$IPY tools/buildstub.py $PYTHON_DLL stub stub')

# compile stub code
# NOTE: nasm Object seems to work fine out of the box
# TODO: use scanner instead of explicit dependency for stubmain.c?
jumps_obj = native.Object('stub/jumps.generated.asm')
stubmain_obj = native.Obj('stub/stubmain.c')
Depends(stubmain_obj, 'stub/stubinit.generated.c')

# build and link python26.dll
cpy_srcs = glommap(lambda x: Glob('stub/%s/*.c' % x), 'Modules Objects Parser Python'.split())
cpy_objs = glommap(native.Obj, cpy_srcs)
native.Dll('build/ironclad/python26.dll', stubmain_obj + jumps_obj + cpy_objs + depend_msvcr90)

#===============================================================================
# test data

native.Dll('tests/data/setvalue.pyd', native.Obj('tests/data/src/setvalue.c') + depend_msvcr90)
native.Dll('tests/data/exportsymbols.dll', native.Obj('tests/data/src/exportsymbols.c') + depend_msvcr90)
native.Dll('tests/data/fakepython25.dll', native.Obj('tests/data/src/fakepython25.c') + depend_msvcr90)
native.Dll('tests/data/implicit-load-msvcr90.dll', native.Obj('tests/data/src/empty.c') + depend_msvcr90)
