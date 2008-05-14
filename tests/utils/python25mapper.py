
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


class ModuleWrapper(object):
    def __init__(self, engine, module):
        self.moduleScope = engine.CreateScope(module.Scope.Dict)
    def __getattr__(self, name):
        return self.moduleScope.GetVariable[object](name)
    def __setattr__(self, name, value):
        if name == 'moduleScope':
            self.__dict__['moduleScope'] = value
            return
        self.moduleScope.SetVariable(name, value)
        

class TempPtrCheckingPython25Mapper(Python25Mapper):
    def __init__(self, *args):
        Python25Mapper.__init__(self, *args)
        self.tempPtrsFreed = False
    def FreeTemps(self):
        Python25Mapper.FreeTemps(self)
        self.tempPtrsFreed = True