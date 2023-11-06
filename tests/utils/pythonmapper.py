from tests.utils.cpython import MakeModuleDef

from System import IntPtr

def MakeAndAddEmptyModule(mapper):
    moduleDef, deallocDef = MakeModuleDef("test_module", IntPtr.Zero, "test_docstring")
    modulePtr = mapper.PyModule_Create2(moduleDef, 12345)
    deallocDef()
    return modulePtr
