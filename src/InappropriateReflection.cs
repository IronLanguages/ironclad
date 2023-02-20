using System;
using System.Collections;
using System.IO;
using System.Reflection;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Runtime;

using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

namespace Ironclad
{
    internal class InappropriateReflection
    {
        public static PythonType
        PythonTypeFromMappingProxy(MappingProxy proxy)
        {
            FieldInfo _typeField = (FieldInfo)(proxy.GetType().GetMember(
                "type", BindingFlags.NonPublic | BindingFlags.Instance)[0]);
            return (PythonType)_typeField.GetValue(proxy);
        }
        
        public static object
        GetPythonException(System.Exception clrException)
        {
            MethodInfo _toPythonMethod = typeof(PythonExceptions).GetMethod(
                "ToPython", BindingFlags.NonPublic | BindingFlags.Static);
            try
            {
                return _toPythonMethod.Invoke(null, new object[] { clrException });
            }
            catch (Exception e)
            {
                throw e.GetBaseException();
            }
        }

        public static void PrintWithDest(CodeContext context, object dest, object o)
        {
            MethodInfo _printWithDestMethod = typeof(PythonOps).GetMethod("PrintWithDest", BindingFlags.NonPublic | BindingFlags.Static);
            try
            {
                _printWithDestMethod.Invoke(null, new object[] { context, dest, o });
            }
            catch (Exception e)
            {
                throw e.GetBaseException();
            }
        }

        public static bool IsInstance(CodeContext context, object o, object typeinfo)
        {
            MethodInfo _isInstanceMethod = typeof(PythonOps).GetMethod("IsInstance", BindingFlags.NonPublic | BindingFlags.Static, null, new [] {typeof(CodeContext), typeof(object), typeof(object)}, null);
            try
            {
                return (bool)_isInstanceMethod.Invoke(null, new object[] { context, o, typeinfo });
            }
            catch (Exception e)
            {
                throw e.GetBaseException();
            }
        }
    }
}
