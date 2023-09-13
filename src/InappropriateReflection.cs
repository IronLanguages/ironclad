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
                "type", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance)[0]);
            return (PythonType)_typeField.GetValue(proxy);
        }
    }
}
