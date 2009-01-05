
from System import IntPtr
from Ironclad import Python25Mapper


def MakeAndAddEmptyModule(mapper):
    modulePtr = mapper.Py_InitModule4(
        "test_module",
        IntPtr.Zero,
        "test_docstring",
        IntPtr.Zero,
        12345
    )
    return modulePtr
