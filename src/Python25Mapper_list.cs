using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Types;

using Ironclad.Structs;


namespace Ironclad
{
    public partial class Python25Mapper : Python25Api
    {
        
        
        public virtual void 
        PyList_Dealloc(IntPtr listPtr)
        {
            PyListObject listStruct = (PyListObject)Marshal.PtrToStructure(listPtr, typeof(PyListObject));
            
            if (listStruct.ob_item != IntPtr.Zero)
            {
                IntPtr itemsPtr = listStruct.ob_item;
                for (int i = 0; i < listStruct.ob_size; i++)
                {
                    IntPtr itemPtr = CPyMarshal.ReadPtr(itemsPtr);
                    if (itemPtr != IntPtr.Zero)
                    {
                        this.DecRef(itemPtr);
                    }
                    itemsPtr = CPyMarshal.Offset(itemsPtr, CPyMarshal.PtrSize);
                }
                this.allocator.Free(listStruct.ob_item);
            }
            PyObject_Free_Delegate freeDgt = (PyObject_Free_Delegate)
                CPyMarshal.ReadFunctionPtrField(
                    this.PyList_Type, typeof(PyTypeObject), "tp_free", typeof(PyObject_Free_Delegate));
            freeDgt(listPtr);
        }
        
        
        private IntPtr
        Store(List list)
        {
            IntPtr listPtr = this.PyList_New(0);
            for (int i = 0; i < list.__len__(); i++)
            {
                IntPtr itemPtr = this.Store(list[i]);
                this.PyList_Append(listPtr, itemPtr);
                this.DecRef(itemPtr);
            }
            return listPtr;
        }
        
        public override IntPtr 
        PyList_New(int length)
        {
            object ipylist = UnmanagedDataMarker.PyListObject;
            PyListObject list = new PyListObject();
            list.ob_refcnt = 1;
            list.ob_type = this.PyList_Type;
            list.ob_size = (uint)length;
            list.allocated = (uint)length;
            
            if (length == 0)
            {
                list.ob_item = IntPtr.Zero;
                ipylist = new List();
            }
            else
            {
                int bytes = length * CPyMarshal.PtrSize;
                list.ob_item = this.allocator.Alloc(bytes);
                CPyMarshal.Zero(list.ob_item, bytes);
            }
            
            IntPtr listPtr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyListObject)));
            Marshal.StructureToPtr(list, listPtr, false);
            this.map.Associate(listPtr, ipylist);
            return listPtr;
        }   
        
        
        private void 
        PyList_Append_Empty(IntPtr listPtr, ref PyListObject listStruct, IntPtr itemPtr)
        {
            listStruct.ob_size = 1;
            listStruct.allocated = 1;
            listStruct.ob_item = this.allocator.Alloc(CPyMarshal.PtrSize);
            CPyMarshal.WritePtr(listStruct.ob_item, itemPtr);
            Marshal.StructureToPtr(listStruct, listPtr, false);
        }
        
        
        private void 
        PyList_Append_NonEmpty(IntPtr listPtr, ref PyListObject listStruct, IntPtr itemPtr)
        {
            uint oldAllocated = listStruct.allocated;
            int oldAllocatedBytes = (int)oldAllocated * CPyMarshal.PtrSize;
            listStruct.ob_size += 1;
            listStruct.allocated += 1;
            IntPtr oldDataStore = listStruct.ob_item;
            
            listStruct.ob_item = this.allocator.Alloc((int)listStruct.allocated * CPyMarshal.PtrSize);
            Unmanaged.memcpy(listStruct.ob_item, oldDataStore, oldAllocatedBytes);
            this.allocator.Free(oldDataStore);
            
            CPyMarshal.WritePtr(CPyMarshal.Offset(listStruct.ob_item, oldAllocatedBytes), itemPtr);
            Marshal.StructureToPtr(listStruct, listPtr, false);
        }
        
        
        public override int 
        PyList_Append(IntPtr listPtr, IntPtr itemPtr)
        {
            PyListObject listStruct = (PyListObject)Marshal.PtrToStructure(listPtr, typeof(PyListObject));
            if (listStruct.ob_item == IntPtr.Zero)
            {
                this.PyList_Append_Empty(listPtr, ref listStruct, itemPtr);
            }
            else
            {
                this.PyList_Append_NonEmpty(listPtr, ref listStruct, itemPtr);
            }
            
            List list = (List)this.Retrieve(listPtr);
            list.append(this.Retrieve(itemPtr));
            this.IncRef(itemPtr);
            return 0;
        }
        
        
        public override int
        PyList_SetItem(IntPtr listPtr, int index, IntPtr itemPtr)
        {
            if (listPtr == IntPtr.Zero)
            {
                this.DecRef(itemPtr);
                return -1;
            }
            bool listPtrValid = this.map.HasPtr(listPtr);
            if (!listPtrValid)
            {
                this.DecRef(itemPtr);
                return -1;
            }
            bool okToContinue = false;
            object ipylist = this.map.GetObj(listPtr);
            List realIpylist = ipylist as List;
            if (realIpylist != null)
            {
                okToContinue = true;
            }
            if (ipylist.GetType() == typeof(UnmanagedDataMarker))
            {
                UnmanagedDataMarker marker = (UnmanagedDataMarker)ipylist;
                if (marker == UnmanagedDataMarker.PyListObject)
                {
                    okToContinue = true;
                }
            }
            if (!okToContinue)
            {
                this.DecRef(itemPtr);
                return -1;
            }
            
            int length = CPyMarshal.ReadIntField(listPtr, typeof(PyListObject), "ob_size");
            if (index < 0 || index >= length)
            {
                this.DecRef(itemPtr);
                return -1;
            }
            
            IntPtr dataPtr = CPyMarshal.ReadPtrField(listPtr, typeof(PyListObject), "ob_item");
            IntPtr oldItemPtrPtr = CPyMarshal.Offset(dataPtr, index * CPyMarshal.PtrSize);
            IntPtr oldItemPtr = CPyMarshal.ReadPtr(oldItemPtrPtr);
            if (oldItemPtr != IntPtr.Zero)
            {
                this.DecRef(oldItemPtr);
            }
            CPyMarshal.WritePtr(oldItemPtrPtr, itemPtr);
            
            if (realIpylist != null)
            {
                object item = this.Retrieve(itemPtr);
                realIpylist[index] = item;
            }      
            return 0;
        }
        
        public override IntPtr
        PyList_GetSlice(IntPtr listPtr, int start, int stop)
        {
            List list = (List)this.Retrieve(listPtr);
            List sliced = (List)list[new Slice(start, stop)];
            IntPtr result = this.Store(sliced);
            return result;
        }
        
                
        private void
        ActualiseList(IntPtr ptr)
        {
            if (this.listsBeingActualised.ContainsKey(ptr))
            {
                throw new Exception("Fatal logic error -- Python25Mapper.listsBeingActualised is somehow corrupt");
            }
            
            List newList = new List();
            this.listsBeingActualised[ptr] = newList;
            
            int length = CPyMarshal.ReadIntField(ptr, typeof(PyListObject), "ob_size");
            if (length != 0)
            {
                IntPtr itemPtrPtr = CPyMarshal.ReadPtrField(ptr, typeof(PyListObject), "ob_item");
                for (int i = 0; i < length; i++)
                {
                    IntPtr itemPtr = CPyMarshal.ReadPtr(itemPtrPtr);
                    if (itemPtr == IntPtr.Zero)
                    {
                        // We have *no* idea what to do here.
                        throw new ArgumentException("Attempted to Retrieve uninitialised PyListObject -- expect strange bugs");
                    }
                    
                    if (this.listsBeingActualised.ContainsKey(itemPtr))
                    {
                        newList.append(this.listsBeingActualised[itemPtr]);
                    }
                    else
                    {
                        newList.append(this.Retrieve(itemPtr));
                    }

                    itemPtrPtr = CPyMarshal.Offset(itemPtrPtr, CPyMarshal.PtrSize);
                }
            }
            this.listsBeingActualised.Remove(ptr);
            this.map.Associate(ptr, newList);
            
        }
    }

}
