
import os
import shutil
import tempfile
from tests.utils.process import spawn
from tests.utils.runtest import makesuite, run
from tests.utils.testcase import TestCase

def write(name, text):
    f = open(name, 'w')
    try:
        f.write(text)
    finally:
        f.close()

class GeneratePythonMapperTest(TestCase):

    def testCreatesPythonMapper_cs(self):
        tempDir = tempfile.mkdtemp()
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
            write("allFunctions", ALL_FUNCTIONS)
            write("pythonMapperDataItems", DATA_ITEMS)
            write("pythonMapperDataPtrItems", DATA_PTR_ITEMS)
            write("Py_InitModule4.pmdi", PY_INITMODULE4)
            write("PyModule_AddObject.pmdi", PYMODULE_ADDOBJECT)

            retVal = spawn("ipy", toolPath)
            self.assertEquals(retVal, 0, "process ended badly")

            os.chdir(testBuildDir)
            f = open("PythonMapper.cs", 'r')
            try:
                result = f.read()
                for (i, (a, e)) in enumerate(zip(result, EXPECTED_OUTPUT)):
                    if a != e:
                        print "first failure at", i, a, e
                        print ">>>%s<<<\n>>>%s<<<" % (result[i:], EXPECTED_OUTPUT[i:])
                        self.fail()
                self.assertEquals(result, EXPECTED_OUTPUT, "generated wrong")
            finally:
                f.close()

        finally:
            os.chdir(origCwd)
        shutil.rmtree(tempDir)


ALL_FUNCTIONS = """
Py_InitModule4
Some_NotImplemented_Function
PyModule_AddObject
SomeOther_NotImplemented_Function
"""

PY_INITMODULE4 = """
IntPtr
string name, IntPtr methods, string doc, IntPtr self, int apiver
return IntPtr.Zero"""

PYMODULE_ADDOBJECT = """int
IntPtr module, string name, IntPtr item
return 0
"""

DATA_ITEMS = """
PyString_Type PyTypeObject
PyType_Type PyTypeObject
Py_Something int
"""

DATA_PTR_ITEMS = """
PyExc_SystemError
PyExc_TypeError
"""


EXPECTED_OUTPUT = """
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

using Ironclad.Structs;

namespace Ironclad
{

    public class PythonMapper
    {
        protected Dictionary<string, Delegate> dgtMap = new Dictionary<string, Delegate>();
        private Dictionary<string, IntPtr> dataMap = new Dictionary<string, IntPtr>();
    
        [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
        public delegate void CPython_null_Delegate();

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

        public void SomeOther_NotImplemented_Function()
        {
            throw new NotImplementedException("called SomeOther_NotImplemented_Function -- stack is probably corrupt now");
        }

        public void Some_NotImplemented_Function()
        {
            throw new NotImplementedException("called Some_NotImplemented_Function -- stack is probably corrupt now");
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
                case "SomeOther_NotImplemented_Function":
                    this.dgtMap[name] = new CPython_null_Delegate(this.SomeOther_NotImplemented_Function);
                    break;
                case "Some_NotImplemented_Function":
                    this.dgtMap[name] = new CPython_null_Delegate(this.Some_NotImplemented_Function);
                    break;
                case "PyExc_SystemError":
                    this.dataMap[name] = this.Make_PyExc_SystemError();
                    return this.dataMap[name];
                case "PyExc_TypeError":
                    this.dataMap[name] = this.Make_PyExc_TypeError();
                    return this.dataMap[name];

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
                IntPtr address;
                if (this.dataMap.TryGetValue("PyString_Type", out address))
                {
                    return address;
                }
                return IntPtr.Zero;
            }
        }

        public virtual void Fill_PyType_Type(IntPtr address) { ; }
        public IntPtr PyType_Type
        {
            get
            {
                IntPtr address;
                if (this.dataMap.TryGetValue("PyType_Type", out address))
                {
                    return address;
                }
                return IntPtr.Zero;
            }
        }

        public virtual void Fill_Py_Something(IntPtr address) { ; }
        public IntPtr Py_Something
        {
            get
            {
                IntPtr address;
                if (this.dataMap.TryGetValue("Py_Something", out address))
                {
                    return address;
                }
                return IntPtr.Zero;
            }
        }

        public void SetData(string name, IntPtr address)
        {
            switch (name)
            {
                case "PyString_Type":
                    CPyMarshal.Zero(address, Marshal.SizeOf(typeof(PyTypeObject)));
                    this.Fill_PyString_Type(address);
                    this.dataMap["PyString_Type"] = address;
                    break;
                case "PyType_Type":
                    CPyMarshal.Zero(address, Marshal.SizeOf(typeof(PyTypeObject)));
                    this.Fill_PyType_Type(address);
                    this.dataMap["PyType_Type"] = address;
                    break;
                case "Py_Something":
                    CPyMarshal.Zero(address, Marshal.SizeOf(typeof(int)));
                    this.Fill_Py_Something(address);
                    this.dataMap["Py_Something"] = address;
                    break;
            }
        }
    }
}
"""


suite = makesuite(GeneratePythonMapperTest)

if __name__ == '__main__':
    run(suite)