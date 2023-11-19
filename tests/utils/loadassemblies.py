import sys
import os
import clr

if 'IRONPYTHONPATH' not in os.environ:
    print("*"*80)
    print("WARNING: your IRONPYTHONPATH is not defined.")
    print("As absolute minimum, please set IRONPYTHONPATH to the directory")
    print("containing the ironclad package to test.")
    print("The tests will assume it is in directory 'build'.")
    print("Some of ironclad test assume DLLs dir of cpython is present in IRONPYTHONPATH.")
    print("*"*80)
    sys.path.insert(0, os.path.abspath('build'))

for _ironclad_path in sys.path:
    IRONCLAD_DLL = os.path.join(_ironclad_path, "ironclad" , "ironclad.dll")
    CPYTHONSTUB_DLL = os.path.join(_ironclad_path, "ironclad" , "python34.dll")
    if os.path.exists(IRONCLAD_DLL) and os.path.exists(CPYTHONSTUB_DLL):
        clr.AddReferenceToFileAndPath(IRONCLAD_DLL)
        break
else:
    raise ImportError("Cannot find ironclad.dll with python34.dll")

if 'TESTDATA_BUILDDIR' not in os.environ:
    print("*"*80)
    print("WARNING: TESTDATA_BUILDDIR is not defined.")
    print("This should be the path to the directory containing test data created during build.")
    print("Some of ironclad test load DLLs and PYDs from this directory.")
    print("The tests will assume in-source build location.")
    print("*"*80)

TESTDATA_BUILDDIR = os.environ.get('TESTDATA_BUILDDIR', os.path.join("tests", "data"))

# If we ever completely unload msvcr100.dll, we get weird explosions next time we try to
# load it. This is surely my fault, and it would be nice to make it work 'properly', but
# for now this hack suffices; it shouldn't be an issue in real use because you shouldn't
# be repeatedly creating Mappers.

if sys.platform == 'win32':
    from Ironclad import Unmanaged
    Unmanaged.LoadLibrary(TESTDATA_BUILDDIR + "\\implicit-load-msvcr100.dll")