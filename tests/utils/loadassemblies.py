import sys
import os

from tests.utils.testenv import is_ironpython, is_windows, is_netcoreapp

if len(sys.argv) >= 2 and '/' in sys.argv[-1]:
    _configuration, _framework = sys.argv.pop().split('/', 1)

if '_configuration' in globals():
    TESTDATA_BUILDDIR = os.path.join("build", _configuration, _framework, "tests", "data")
else:
    if 'TESTDATA_BUILDDIR' not in os.environ:
        print("*"*80)
        print("WARNING: TESTDATA_BUILDDIR is not defined.")
        print("This should be the path to the directory containing test data created during build.")
        print("Some of Ironclad tests load DLLs and PYDs from this directory.")
        print("The tests will assume in-source build location.")
        print("*"*80)

    TESTDATA_BUILDDIR = os.environ.get('TESTDATA_BUILDDIR', os.path.join("tests", "data"))


if is_ironpython:
    if 'IRONPYTHONPATH' not in os.environ:
        print("*"*80)
        print("WARNING: your IRONPYTHONPATH is not defined.")
        if '_configuration' not in globals():
            print("Please set IRONPYTHONPATH to the directory")
            print("containing the ironclad package to test.")
            print("The tests will assume it is in directory 'build'.")
        print("Some of Ironclad tests assume DLLs dir of CPython is present in IRONPYTHONPATH.")
        print("*"*80)
    if '_configuration' in globals():
        _ironclad_path = os.path.abspath(os.path.join("out", _configuration, _framework))
    else:
        _ironclad_path = os.path.abspath('build')
    if _ironclad_path not in sys.path:
        sys.path.insert(0, _ironclad_path)

for _ironclad_path in sys.path:
    IRONCLAD_DLL = os.path.join(_ironclad_path, "ironclad" , "ironclad.dll")
    CPYTHONSTUB_DLL = os.path.join(_ironclad_path, "ironclad" , "python34.dll")
    if os.path.exists(IRONCLAD_DLL) and os.path.exists(CPYTHONSTUB_DLL):
        if is_ironpython:
            import clr
            clr.AddReferenceToFileAndPath(IRONCLAD_DLL)
        break
else:
    if is_ironpython:
        raise ImportError("Cannot find ironclad.dll with python34.dll")
    _ironclad_path = None

if is_netcoreapp:
    import clr
    clr.AddReference("System.Core")
    clr.AddReference("System.Collections")

# If we ever completely unload msvcr100.dll, we get weird explosions next time we try to
# load it. This is surely my fault, and it would be nice to make it work 'properly', but
# for now this hack suffices; it shouldn't be an issue in real use because you shouldn't
# be repeatedly creating Mappers.

if is_windows and is_ironpython:
    from Ironclad import Unmanaged
    Unmanaged.LoadLibrary(TESTDATA_BUILDDIR + "\\implicit-load-msvcr100.dll")