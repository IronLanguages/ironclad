using Microsoft.Scripting;
using Microsoft.Scripting.Hosting;
using System.Reflection;
using IronPython.Runtime;

namespace TestUtils
{
    public class ExecUtils
    {
        private static PythonContext
        GetPythonContext(ScriptEngine engine)
        {
            FieldInfo _languageField = (FieldInfo)(engine.GetType().GetMember(
                "_language", BindingFlags.NonPublic | BindingFlags.Instance)[0]);
            return (PythonContext)_languageField.GetValue(engine);
        }

        public static void
        Exec(ScriptEngine engine, string code)
        {
            ScriptSource script = engine.CreateScriptSourceFromString(code, SourceCodeKind.Statements);
            ScriptScope scope = engine.CreateScope(GetPythonContext(engine).SystemState.Dict);
            script.Execute(scope);
        }
        
        public static object
        GetPythonModule(ScriptEngine engine, string name)
        {
            return engine.Runtime.Globals.GetVariable(name);
        }
    }
}
