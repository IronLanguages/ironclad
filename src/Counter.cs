using System;

using IronPython.Runtime;

namespace Ironclad
{
    internal class Counter
    {
        private int value = 0;

        public int Value
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