using System;
using System.IO;
using System.Reflection;

using IronPython.Runtime;

namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        public override IntPtr PyFile_AsFile(IntPtr pyFilePtr)
        {
            PythonFile pyFile = (PythonFile)this.Retrieve(pyFilePtr);
            FieldInfo streamField = (FieldInfo)(pyFile.GetType().GetMember(
                "_stream", BindingFlags.NonPublic | BindingFlags.Instance)[0]);
            FileStream stream = (FileStream)streamField.GetValue(pyFile);
            IntPtr handle = stream.SafeFileHandle.DangerousGetHandle();
            int fd = Unmanaged._open_osfhandle(handle, 0);
            
            if (stream.CanWrite)
            {
                return Unmanaged._fdopen(fd, "w");
            }
            return Unmanaged._fdopen(fd, "r");
        }        
    }

}
