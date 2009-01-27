using System;
using System.Runtime.InteropServices;

using Ironclad.Structs;

namespace Ironclad
{
    public class OpaquePyCObject
    {
        private Python25Mapper mapper;
        private IntPtr instancePtr;
        
        public OpaquePyCObject(Python25Mapper inMapper, IntPtr inInstancePtr)
        {
            this.mapper = inMapper;
            this.instancePtr = inInstancePtr;
        }
        
        ~OpaquePyCObject()
        {
            if (this.mapper.Alive)
            {
                this.mapper.DecRef(this.instancePtr);
            }
        }
    }

    public class OpaquePyCell
    {
        // no, this really doesn't do anything, at all
    }
}
