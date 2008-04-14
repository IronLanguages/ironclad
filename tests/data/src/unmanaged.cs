using System;
using System.Runtime.InteropServices;

namespace Unmanaged
{
    public class msvcrt
    {
        [DllImport("msvcr71.dll")]
        public static extern int fread(IntPtr buf, int size, int count, IntPtr file);
        
        [DllImport("msvcr71.dll")]
        public static extern int fwrite(IntPtr buf, int size, int count, IntPtr file);

        [DllImport("msvcr71.dll")]
        public static extern int fclose(IntPtr file);
    }
}