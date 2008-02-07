using System;
using System.Runtime.InteropServices;


namespace JumPyTestUtils
{
    public class PythonStubHarness
    {

        [DllImport("build\\python25.dll")]
        private static extern int 
        PyArg_ParseTupleAndKeywords(IntPtr args, IntPtr kwargs, string format, IntPtr kwlist, __arglist);


        public static int 
        Test_PA_PTAK__1arg(
            IntPtr args, IntPtr kwargs, string format, IntPtr kwlist, IntPtr arg1)
        {
            return PyArg_ParseTupleAndKeywords(args, kwargs, format, kwlist,
                __arglist(arg1));
        }

        public static int 
        Test_PA_PTAK__2arg(
            IntPtr args, IntPtr kwargs, string format, IntPtr kwlist, IntPtr arg1, IntPtr arg2)
        {
            return PyArg_ParseTupleAndKeywords(args, kwargs, format, kwlist,
                __arglist(arg1, arg2));
        }

        public static int 
        Test_PA_PTAK__3arg(
            IntPtr args, IntPtr kwargs, string format, IntPtr kwlist, IntPtr arg1, IntPtr arg2, IntPtr arg3)
        {
            return PyArg_ParseTupleAndKeywords(args, kwargs, format, kwlist,
                __arglist(arg1, arg2, arg3));
        }

    }
}