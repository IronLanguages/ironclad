using System;
using System.Collections.Generic;

using IronPython.Runtime;
using Microsoft.Scripting.Hosting;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        public PythonModule
        DispatcherModule
        {
            get
            {
                return this.dispatcherModule;
            }
        }

        private void CreateDispatcherModule()
        {
            string id = "_ironclad_dispatcher";

            Dictionary<string, object> globals = new Dictionary<string, object>();
            globals["IntPtr"] = typeof(IntPtr);
            globals["CPyMarshal"] = typeof(CPyMarshal);
            globals["NullReferenceException"] = typeof(NullReferenceException);

            this.dispatcherModule = this.GetPythonContext().CreateModule(
                id, id, globals, ModuleOptions.None);
            this.ExecInModule(FIX_CPyMarshal_RuntimeType_CODE, this.dispatcherModule);
            this.ExecInModule(DISPATCHER_MODULE_CODE, this.dispatcherModule);
            
            ScriptScope scope = this.GetModuleScriptScope(this.dispatcherModule);
            this.dispatcherClass = scope.GetVariable<object>("Dispatcher");
        }
        
        private const string DISPATCHER_MODULE_CODE = @"
class Dispatcher(object):

    def __init__(self, mapper, table):
        self.mapper = mapper
        self.table = table

    def _maybe_raise(self, resultPtr):
        error = self.mapper.LastException
        if error:
            self.mapper.LastException = None
            raise error
        if resultPtr == IntPtr(0):
            raise NullReferenceException('CPython callable returned null without setting an exception')

    def _surely_raise(self, fallbackError):
        error = self.mapper.LastException
        if error:
            self.mapper.LastException = None
            raise error
        raise fallbackError

    def _cleanup(self, *args):
        self.mapper.FreeTemps()
        for arg in args:
            if arg != IntPtr(0):
                self.mapper.DecRef(arg)
    

    def construct(self, name, klass, *args, **kwargs):
        instance = object.__new__(klass)
        argsPtr = self.mapper.Store(args)
        kwargsPtr = self.mapper.Store(kwargs)
        instancePtr = self.table[name](klass._typePtr, argsPtr, kwargsPtr)
        try:
            self._maybe_raise(instancePtr)
        finally:
            self._cleanup(argsPtr, kwargsPtr)
        
        if self.mapper.HasPtr(instancePtr):
            self.mapper.IncRef(instancePtr)
            return self.mapper.Retrieve(instancePtr)
        
        instance._instancePtr = instancePtr
        self.mapper.StoreBridge(instancePtr, instance)
        self.mapper.Strengthen(instance)
        return instance

    def init(self, name, instance, *args, **kwargs):
        if not self.table.has_key(name):
            return
        argsPtr = self.mapper.Store(args)
        kwargsPtr = self.mapper.Store(kwargs)
        result = self.table[name](instance._instancePtr, argsPtr, kwargsPtr)
        self._cleanup(argsPtr, kwargsPtr)
            
        if result < 0:
            self._surely_raise(Exception('%s failed; object is probably not safe to use' % name))

    def delete(self, instance):
        if self.mapper.Alive:
            self.mapper.CheckBridgePtrs()
            self.mapper.DecRef(instance._instancePtr)


    def function_noargs(self, name):
        return self.method_noargs(name, IntPtr(0))

    def method_noargs(self, name, instancePtr):
        resultPtr = self.table[name](instancePtr, IntPtr(0))
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr)

    def function_objarg(self, name, arg):
        return self.method_objarg(name, IntPtr(0), arg)
        
    def method_objarg(self, name, instancePtr, arg):
        argPtr = self.mapper.Store(arg)
        resultPtr = self.table[name](instancePtr, argPtr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr, argPtr)

    def function_varargs(self, name, *args):
        return self.method_varargs(name, IntPtr(0), *args)

    def method_varargs(self, name, instancePtr, *args):
        argsPtr = self.mapper.Store(args)
        resultPtr = self.table[name](instancePtr, argsPtr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr, argsPtr)

    def function_kwargs(self, name, *args, **kwargs):
        return self.method_kwargs(name, IntPtr(0), *args, **kwargs)

    def method_kwargs(self, name, instancePtr, *args, **kwargs):
        argsPtr = self.mapper.Store(args)
        kwargsPtr = IntPtr(0)
        if kwargs != {}:
            kwargsPtr = self.mapper.Store(kwargs)
        resultPtr = self.table[name](instancePtr, argsPtr, kwargsPtr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr, argsPtr, kwargsPtr)
    
    def method_selfarg(self, name, instancePtr, errorHandler=None):
        resultPtr = self.table[name](instancePtr)
        try:
            if errorHandler:
                errorHandler(resultPtr)
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr)

    def method_ssizearg(self, name, instancePtr, i):
        resultPtr = self.table[name](instancePtr, i)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr)

    def method_getter(self, name, instancePtr, closurePtr):
        resultPtr = self.table[name](instancePtr, closurePtr)
        try:
            self._maybe_raise(resultPtr)
            return self.mapper.Retrieve(resultPtr)
        finally:
            self._cleanup(resultPtr)

    def method_setter(self, name, instancePtr, value, closurePtr):
        valuePtr = self.mapper.Store(value)
        result = self.table[name](instancePtr, valuePtr, closurePtr)
        self._cleanup(valuePtr)
        if result < 0:
            self._surely_raise(Exception('%s failed' % name))


    def set_member_int(self, address, value):
        CPyMarshal.WriteInt(address, value)

    def get_member_int(self, address):
        return CPyMarshal.ReadInt(address)

    def set_member_char(self, address, value):
        CPyMarshal.WriteByte(address, ord(value))

    def get_member_char(self, address):
        return chr(CPyMarshal.ReadByte(address))

    def set_member_ubyte(self, address, value):
        CPyMarshal.WriteByte(address, value)

    def get_member_ubyte(self, address):
        return CPyMarshal.ReadByte(address)

    def set_member_object(self, address, value):
        valuePtr = self.mapper.Store(value)
        oldvPtr = CPyMarshal.ReadPtr(address)
        CPyMarshal.WritePtr(address, valuePtr)
        if oldvPtr != IntPtr(0):
            self.mapper.DecRef(oldvPtr)

    def get_member_object(self, address):
        valuePtr = CPyMarshal.ReadPtr(address)
        if valuePtr != IntPtr(0):
            return self.mapper.Retrieve(valuePtr)

";
    }
}
