
using System;
using System.Runtime.InteropServices;


namespace JumPy
{
    public delegate IntPtr CPythonVarargsFunction_Delegate(IntPtr self, IntPtr args);

    public delegate IntPtr CPythonVarargsKwargsFunction_Delegate(IntPtr self, IntPtr args, IntPtr kwargs);


	namespace Structs
	{
		[Flags]
		public enum METH : uint
		{
			OLDARGS = 0,
			VARARGS = 0x00000001,
			KEYWORDS = 0x00000002,
			NOARGS = 0x00000004,
			O = 0x00000008,
			CLASS = 0x00000010,
			STATIC = 0x00000020,
			COEXIST = 0x00000040,
		}
		
		[StructLayout(LayoutKind.Sequential, Pack=1)]
		public struct PyMethodDef
		{
			public string ml_name;
			public IntPtr ml_meth;
			public METH ml_flags;
			public string ml_doc;

			public PyMethodDef(string name, IntPtr meth, METH flags, string doc)
			{
				this.ml_name = name;
				this.ml_meth = meth;
				this.ml_flags = flags;
				this.ml_doc = doc;
			}
		}


		[StructLayout(LayoutKind.Sequential, Pack=1)]
		public struct PyStringObject
		{
			public uint ob_refcnt;
			public IntPtr ob_type;
			public uint ob_size;
			public int ob_shash;
			public int ob_sstate;
			public byte ob_sval;
		}

	}
}

