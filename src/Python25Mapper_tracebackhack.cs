
using System;

namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        // TODO: these are just-implemented-enough to allow
        // __Pyx_AddTraceback to work, for a given value of 
        // 'work'
    
        public override IntPtr
        PyCode_New(int _0, int _1, int _2, int _3, 
                   IntPtr _4, IntPtr _5, IntPtr _6, IntPtr _7, 
                   IntPtr _8, IntPtr _9, IntPtr _10, IntPtr funcname, 
                   int _12, IntPtr _13)
        {
            this.IncRef(funcname); // the funcname passed into __Pyx_AddTraceback
            return funcname;
        }
        
        public override IntPtr
        PyFrame_New(IntPtr _0, IntPtr code, IntPtr _2, IntPtr _3)
        {
            this.IncRef(code);
            return code;
        }
        
        public override IntPtr
        PyThreadState_Get()
        {
            return IntPtr.Zero;
        }
        
        public override void
        PyTraceBack_Here(IntPtr frame)
        {
            Console.WriteLine("PyTraceBack_Here: {0}", this.Retrieve(frame));
        }
    }
}
