
from System import IntPtr
from JumPy import Python25Mapper


def MakeAndAddEmptyModule(mapper):
    modulePtr = mapper.Py_InitModule4(
        "test_module",
        IntPtr.Zero,
        "test_docstring",
        IntPtr.Zero,
        12345
    )
    return modulePtr


class TempPtrCheckingPython25Mapper(Python25Mapper):
    def __init__(self, *args):
        Python25Mapper.__init__(self, *args)
        self.tempPtrsFreed = False
    def FreeTemps(self):
        Python25Mapper.FreeTemps(self)
        self.tempPtrsFreed = True