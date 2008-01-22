using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

namespace JumPy
{
    class DelegateFP
    {
        private Delegate dgt;
        private GCHandle gch;
        public IntPtr fp;
        public DelegateFP(Delegate dgt)
        {
            this.dgt = dgt;
            this.gch = GCHandle.Alloc(this.dgt);
            this.fp = Marshal.GetFunctionPointerForDelegate(this.dgt);
        }
    }

    class FunctionPointerStore
    {
        Hashtable dict;
        public FunctionPointerStore()
        {
            this.dict = new Hashtable();
        }

        public bool Has(string name)
        {
            return this.dict.ContainsKey(name);
        }

        public void Add(string name, Delegate del)
        {
            if (this.Has(name))
            {
                return;
            }
            this.dict.Add(name, new DelegateFP(del));
        }

        public IntPtr Get(string name)
        {
            if (!this.Has(name))
            {
                return IntPtr.Zero;
            }
            DelegateFP dfp = (DelegateFP)this.dict[name];
            return dfp.fp;
        }
    }
}
