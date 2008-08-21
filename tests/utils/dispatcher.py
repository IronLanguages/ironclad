

def GetDispatcherClass(mapper):
    moduleDict = mapper.DispatcherModule.Scope.Dict
    moduleScope = mapper.Engine.CreateScope(moduleDict)
    return moduleScope.GetVariable[object]("Dispatcher")
