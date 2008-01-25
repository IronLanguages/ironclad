
import unittest

from System import IntPtr
from System.Runtime.InteropServices import Marshal
from JumPy import METH, PyMethodDef, Python25Mapper, StubReference
from IronPython.Hosting import PythonEngine

class Python25MapperTest(unittest.TestCase):

    def test_Py_InitModule4_CreatesModuleInSys(self):
        engine = PythonEngine()
        mapper = Python25Mapper(engine)

        method1 = PyMethodDef(
            "harold",
            IntPtr.Zero,
            METH.VARARGS,
            "harold's documentation",
        )
        size = Marshal.SizeOf(PyMethodDef)
        methods = Marshal.AllocHGlobal(size * 2)
        try:
            Marshal.StructureToPtr(method1, methods, False)
            terminator = IntPtr(methods.ToInt32() + size)
            Marshal.WriteInt64(terminator, 0)

            mapper.Py_InitModule4(
                "test_module",
                methods,
                "test_docstring",
                IntPtr.Zero,
                12345
            )

            test_module = engine.Sys.modules['test_module']
            self.assertEquals(test_module.__doc__, 'test_docstring',
                              'module docstring not remembered')
            self.assertTrue(callable(test_module.harold),
                            'function not remembered')
            self.assertEquals(test_module.harold.__doc__, "harold's documentation",
                              'function docstring not remembered')

        finally:
            Marshal.FreeHGlobal(methods)



suite = unittest.TestSuite()
loader = unittest.TestLoader()
suite.addTest(loader.loadTestsFromTestCase(Python25MapperTest))

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)