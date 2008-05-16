using System;
using System.Collections.Generic;

namespace Ironclad
{
    
    internal class StupidSet
    {
        private Dictionary<object, string> store = new Dictionary<object, string>();
        
        public void Add(object obj)
        {
            this.store[obj] = "stupid";
        }
        
        public void SetRemove(object obj)
        {
            if (!this.store.Remove(obj))
            {
                throw new KeyNotFoundException();
            }
        }
        
        public void RemoveIfPresent(object obj)
        {
            this.store.Remove(obj);
        }
        
        public object[] ElementsArray
        {
            get
            {
                object[] result = new object[this.store.Count];
                this.store.Keys.CopyTo(result, 0);
                return result;
            }
        }
    }
}