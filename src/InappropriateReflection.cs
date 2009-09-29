using System;
using System.Collections;
using System.IO;
using System.Reflection;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Runtime;

using IronPython.Runtime;
using IronPython.Runtime.Exceptions;
using IronPython.Runtime.Types;

namespace Ironclad
{
    internal class InappropriateReflection
    {
        public static FileStream
        StreamFromPythonFile(PythonFile pyFile)
        {
            FieldInfo streamField = (FieldInfo)(pyFile.GetType().GetMember(
                "_stream", BindingFlags.NonPublic | BindingFlags.Instance)[0]);
            return (FileStream)streamField.GetValue(pyFile);
        }
        
        public static PythonType
        PythonTypeFromDictProxy(DictProxy proxy)
        {
            FieldInfo _typeField = (FieldInfo)(proxy.GetType().GetMember(
                "_dt", BindingFlags.NonPublic | BindingFlags.Instance)[0]);
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
    }
}
