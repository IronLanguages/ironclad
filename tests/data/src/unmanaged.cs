using System;
using System.Runtime.InteropServices;

namespace TestUtils
{
    public class Unmanaged
    {
        [DllImport("msvcr71.dll")]
        public static extern int fread(IntPtr buf, int size, int count, IntPtr file);
        
        [DllImport("msvcr71.dll")]
        public static extern int fwrite(IntPtr buf, int size, int count, IntPtr file);

        [DllImport("msvcr71.dll")]
        public static extern int fclose(IntPtr file);

        [DllImport("msvcr71.dll")]
        public static extern int fflush(IntPtr file);

        [DllImport("msvcr71.dll")]
        public static extern long _get_osfhandle(int fd);
    }
}
