using Microsoft.CSharp;
using System;
using System.CodeDom.Compiler;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;

namespace JumPy
{
    public class CPythonModuleImporter
    {
        private CSharpCodeProvider compiler;
        private CompilerParameters options;

        public CPythonModuleImporter()
        {
            this.compiler = new CSharpCodeProvider();
            this.options = new CompilerParameters();
            this.options.GenerateInMemory = true;
        }

        private string codeTemplate =
            "using System.Runtime.InteropServices;\n" +
            "public class {0:s} {{\n" +
            "  [DllImport(\"{1:s}\")]\n" +
            "  private static extern void {2:s}();\n" +
            "  public {0:s}() {{\n" +
            "    {2:s}();\n" +
            "  }}\n" +
            "}}\n";

        public Object ImportModule(string dllPath)
        {
            string name = Path.GetFileNameWithoutExtension(dllPath);
            string initName = String.Format("init{0:s}", name);
            string escapedDllPath = dllPath.Replace("\\", "\\\\");
            string code = String.Format(this.codeTemplate, 
                new string[] { name, escapedDllPath, initName });
            return this.CompileAndInstantiate(name, code);
        }

        public Object CompileAndInstantiate(string name, string csharpClass)
        {
            string[] codeHolder = new string[] { csharpClass };
            CompilerResults results =
                this.compiler.CompileAssemblyFromSource(this.options, codeHolder);
            return results.CompiledAssembly.CreateInstance(name);
        }
    }
}
