import locale
import os
import sys
import subprocess
import unittest
import tests.utils.loadassemblies
import System

from tests.utils.gc import gcwait
from tests.utils.memory import CreateTypes

from Ironclad import PythonMapper, Unmanaged

class TrivialMapperSubclass(PythonMapper):
    pass


def _WithMapper(func, mapperCls):
    def patched(*args):
        mapper = mapperCls()
        deallocTypes = CreateTypes(mapper)
        deallocs = [mapper.Dispose, deallocTypes]
        newArgs = args + (mapper, deallocs.append)
        mapper.EnsureGIL()
        try:
            return func(*newArgs)
        finally:
            mapper.ReleaseGIL()
            for dealloc in deallocs:
                dealloc()
    return patched

WithMapper = lambda f: _WithMapper(f, PythonMapper)
WithMapperSubclass = lambda f: _WithMapper(f, TrivialMapperSubclass)


class my_stderr(object):
    def __init__(self, calls):
        self.calls = calls
    def write(self, *args):
        self.calls.append(args)

def WithPatchedStdErr(func):
    def patched(*args):
        calls = []
        old = sys.stderr
        sys.stderr = my_stderr(calls)
        newArgs = args + (calls,)
        try:
            return func(*newArgs)
        finally:
            sys.stderr = old
    return patched
    


class TestCase(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.testDataBuildDir = tests.utils.loadassemblies.TESTDATA_BUILDDIR
        self.libPre = tests.utils.loadassemblies.DLL_PREFIX
        self.dllExt = tests.utils.loadassemblies.DLL_SUFFIX
        self.pydExt = tests.utils.loadassemblies.PYD_SUFFIX

    def tearDown(self):
        gcwait()
        unittest.TestCase.tearDown(self)
        
        
    def assertMapperHasError(self, mapper, error):
        if error:
            self.assertEqual(isinstance(mapper.LastException, error), True, "wrong error set on mapper")
            mapper.LastException = None
        else:
            self.assertEqual(mapper.LastException, None)

    def assertRaisesClr(self, ClrException, callable, *args, **kwargs):
        # clr based exception without explicit python equivalent surface as Exception
        # with clsException set to the original exception
        try:
            with self.assertRaises(Exception) as cm:
                callable(*args, **kwargs)
            if not issubclass(type(cm.exception.clsException), ClrException):
                raise cm.exception
        except TestCase.failureException:
            raise self.failureException("{0} not raised".format(ClrException))

    def assertEqual(self, first, second, msg=None):
        if isinstance(first, System.IntPtr): first = first.ToInt64()
        if isinstance(second, System.IntPtr): second = second.ToInt64()
        if isinstance(first, System.UIntPtr): first = first.ToUInt64()
        if isinstance(second, System.UIntPtr): second = second.ToUInt64()
        if type(first) is type(second) and isinstance(first, (tuple, list)):
            self.assertEqual(len(first), len(second), msg)
            for i in range(len(first)):
                self.assertEqual(first[i], second[i], msg)
            return

        super(TestCase, self).assertEqual(first, second, msg)

    def assertEquals(self, first, second, msg=None):
        self.assertEqual(first, second, msg)

    def assertIsLibraryLoaded(self, name, message=None):
        self.assertTrue(self._isLibraryLoaded(name), message)

    def assertIsLibraryNotLoaded(self, name, message=None):
        self.assertFalse(self._isLibraryLoaded(name), message)

    def _isLibraryLoaded(self, name):
        if os.name == 'nt':
            return Unmanaged.GetModuleHandle(name) != System.IntPtr.Zero;

        name = os.path.abspath(name)

        ls = subprocess.check_output(['lsof', '-p', str(os.getpid())]).decode(locale.getpreferredencoding(False)).split(os.linesep)

        pos = ls[0].index('NAME')
        for l in ls[1:]:
            if l[pos:] == name:
                return True

        return False
