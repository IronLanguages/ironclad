using System;
using System.Collections;
using System.IO;
using System.Reflection;

using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using Microsoft.Scripting.Runtime;

using IronPython.Runtime;
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

        public static IEnumerator
        CreateItemEnumerator(object obj)
        {
            MethodInfo _createMethod = typeof(ItemEnumerator).GetMethod(
                "Create", BindingFlags.NonPublic | BindingFlags.Static);
            try
            {
                return (IEnumerator)_createMethod.Invoke(null, new object[] { obj });
            }
            catch (Exception e)
            {
                throw e.GetBaseException();
            }
        }
        
        public static object
        ImportReflected(CodeContext ctx, string name)
        {
            MethodInfo _importMethod = typeof(Importer).GetMethod(
                "ImportReflected", BindingFlags.NonPublic | BindingFlags.Static);
            try
            {
                return _importMethod.Invoke(null, new object[] { ctx, name });
            }
            catch (Exception e)
            {
                throw e.GetBaseException();
            }
        }
    }
}
