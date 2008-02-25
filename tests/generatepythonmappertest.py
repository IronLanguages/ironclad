
import os
import shutil
import tempfile
import unittest
from tests.utils.process import spawn
from tests.utils.runtest import makesuite, run

def write(name, text):
    f = open(name, 'w')
    try:
        f.write(text)
    finally:
        f.close()



class GeneratePythonMapperTest(unittest.TestCase):

    def testCreatesPythonMapper_cs(self):
        tempDir = tempfile.gettempdir()
        testBuildDir = os.path.join(tempDir, 'generatepythonmappertest')
        if os.path.exists(testBuildDir):
            shutil.rmtree(testBuildDir)
        os.mkdir(testBuildDir)
        testSrcDir = os.path.join(testBuildDir, 'pythonmapper_components')
        os.mkdir(testSrcDir)

        origCwd = os.getcwd()
        toolPath = os.path.join(origCwd, "tools/generatepythonmapper.py")

        os.chdir(testSrcDir)
        try:
            write("pythonMapperDataItems", DATA_ITEMS)
            write("pythonMapperDataPtrItems", DATA_PTR_ITEMS)
            write("Py_InitModule4.pythonMapperDelegateItem", PY_INITMODULE4)
            write("PyModule_AddObject.pythonMapperDelegateItem", PYMODULE_ADDOBJECT)

            retVal = spawn("ipy", toolPath)
            self.assertEquals(retVal, 0, "process ended badly")

            os.chdir(testBuildDir)
            f = open("PythonMapper.cs", 'r')
            try:
                result = f.read()
                self.assertEquals(result, EXPECTED_OUTPUT, "generated wrong")
            finally:
                f.close()

        finally:
            os.chdir(origCwd)


PY_INITMODULE4 = """
IntPtr
string name, IntPtr methods, string doc, IntPtr self, int apiver
return IntPtr.Zero"""

PYMODULE_ADDOBJECT = """int
IntPtr module, string name, IntPtr item
return 0
"""

DATA_ITEMS = """
PyString_Type
PyType_Type
"""

DATA_PTR_ITEMS = """
PyExc_SystemError
PyExc_TypeError
"""


EXPECTED_OUTPUT = """
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

namespace Ironclad
{

    public class PythonMapper
    {
        private Dictionary<string, Delegate> dgtMap = new Dictionary<string, Delegate>();
        private Dictionary<string, IntPtr> dataMap = new Dictionary<string, IntPtr>();

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate int PyModule_AddObject_Delegate(IntPtr module, string name, IntPtr item);
        public virtual int PyModule_AddObject(IntPtr module, string name, IntPtr item)
        {
            return 0;
        }

        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate IntPtr Py_InitModule4_Delegate(string name, IntPtr methods, string doc, IntPtr self, int apiver);
        public virtual IntPtr Py_InitModule4(string name, IntPtr methods, string doc, IntPtr self, int apiver)
        {
            return IntPtr.Zero;
        }

        public virtual IntPtr Make_PyExc_SystemError() { return IntPtr.Zero; }
        public IntPtr PyExc_SystemError
        {
            get
            {
                return this.dataMap["PyExc_SystemError"];
            }
        }

        public virtual IntPtr Make_PyExc_TypeError() { return IntPtr.Zero; }
        public IntPtr PyExc_TypeError
        {
            get
            {
                return this.dataMap["PyExc_TypeError"];
            }
        }

        public IntPtr GetAddress(string name)
        {
            if (this.dgtMap.ContainsKey(name))
            {
                return Marshal.GetFunctionPointerForDelegate(this.dgtMap[name]);
            }

            switch (name)
            {
                case "PyModule_AddObject":
                    this.dgtMap[name] = new PyModule_AddObject_Delegate(this.PyModule_AddObject);
                    break;
                case "Py_InitModule4":
                    this.dgtMap[name] = new Py_InitModule4_Delegate(this.Py_InitModule4);
                    break;
                case "PyExc_SystemError":
                    IntPtr address = this.Make_PyExc_SystemError();
                    this.dataMap[name] = address;
                    return address;
                case "PyExc_TypeError":
                    IntPtr address = this.Make_PyExc_TypeError();
                    this.dataMap[name] = address;
                    return address;

                default:
                    return IntPtr.Zero;
            }
            return Marshal.GetFunctionPointerForDelegate(this.dgtMap[name]);
        }


        public virtual void Fill_PyString_Type(IntPtr address) { ; }
        public IntPtr PyString_Type
        {
            get
            {
                return this.dataMap["PyString_Type"];
            }
        }

        public virtual void Fill_PyType_Type(IntPtr address) { ; }
        public IntPtr PyType_Type
        {
            get
            {
                return this.dataMap["PyType_Type"];
            }
        }

        public void SetData(string name, IntPtr address)
        {
            switch (name)
            {
                case "PyString_Type":
                    this.Fill_PyString_Type(address);
                    this.dataMap["PyString_Type"] = address;
                    break;
                case "PyType_Type":
                    this.Fill_PyType_Type(address);
                    this.dataMap["PyType_Type"] = address;
                    break;
            }
        }
    }
}
"""


suite = makesuite(GeneratePythonMapperTest)

if __name__ == '__main__':
    run(suite)