using System;

using IronPython.Runtime;

namespace Ironclad
{
    // not well named :(
    internal class ThreadLocalCounter
    {
        private int value = 0;

        public int Count
        {
            get { return this.value; }
        }

        public void
        Increment()
        {
            this.value += 1;
        }

        public void
        Decrement()
        {
            this.value -= 1;
        }

        public void
        Reset()
        {
            this.value = 0;
        }

    }
}