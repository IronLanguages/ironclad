using System;

using IronPython.Runtime;

namespace Ironclad
{
    // not well named :(
    internal class ThreadLocalDict
    {
        private PythonMapper mapper;
        private PythonDictionary dict;
        private IntPtr ptr;
        
        public ThreadLocalDict(PythonMapper mapper)
        {
            this.mapper = mapper;
            this.dict = new PythonDictionary();
            this.ptr = this.mapper.Store(this.dict);
        }

        ~ThreadLocalDict()
        {
            this.mapper.DecRef(this.ptr);
        }

        public IntPtr
        Ptr
        {
            get { return this.ptr; }
        }

    }
}