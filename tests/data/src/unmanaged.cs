using System;
using System.Runtime.InteropServices;

namespace Unmanaged
{
    public class msvcrt
    {
        [DllImport("msvcrt.dll")]
        public static extern int fread(IntPtr buf, int size, int count, IntPtr file);

        [DllImport("msvcrt.dll")]
        public static extern int fclose(IntPtr file);
    }
}