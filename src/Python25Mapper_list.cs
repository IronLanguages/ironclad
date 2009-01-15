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
        IC_PyList_Dealloc(IntPtr listPtr)
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
            int length = list.__len__();
            PyListObject listStruct = new PyListObject();
            listStruct.ob_refcnt = 1;
            listStruct.ob_type = this.PyList_Type;
            listStruct.ob_size = (uint)length;
            listStruct.allocated = (uint)length;

            int bytes = length * CPyMarshal.PtrSize;
            IntPtr data = this.allocator.Alloc(bytes);
            listStruct.ob_item = data;
            for (int i = 0; i < length; i++)
            {
                CPyMarshal.WritePtr(data, this.Store(list[i]));
                data = CPyMarshal.Offset(data, CPyMarshal.PtrSize);
            }

            IntPtr listPtr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyListObject)));
            Marshal.StructureToPtr(listStruct, listPtr, false);
            this.map.Associate(listPtr, list);
            return listPtr;

        }

        private IntPtr
        IC_PyList_New_Zero()
        {
            PyListObject list = new PyListObject();
            list.ob_refcnt = 1;
            list.ob_type = this.PyList_Type;
            list.ob_size = 0;
            list.allocated = 0;
            list.ob_item = IntPtr.Zero;

            IntPtr listPtr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyListObject)));
            Marshal.StructureToPtr(list, listPtr, false);
            this.map.Associate(listPtr, new List());
            return listPtr;
        }

        public override IntPtr 
        PyList_New(int length)
        {
            if (length == 0)
            {
                return this.IC_PyList_New_Zero();
            }

            PyListObject list = new PyListObject();
            list.ob_refcnt = 1;
            list.ob_type = this.PyList_Type;
            list.ob_size = (uint)length;
            list.allocated = (uint)length;
            
            int bytes = length * CPyMarshal.PtrSize;
            list.ob_item = this.allocator.Alloc(bytes);
            CPyMarshal.Zero(list.ob_item, bytes);
            
            IntPtr listPtr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyListObject)));
            Marshal.StructureToPtr(list, listPtr, false);
            this.incompleteObjects[listPtr] = UnmanagedDataMarker.PyListObject;
            return listPtr;
        }   
        
        
        private void 
        IC_PyList_Append_Empty(IntPtr listPtr, ref PyListObject listStruct, IntPtr itemPtr)
        {
            listStruct.ob_size = 1;
            listStruct.allocated = 1;
            listStruct.ob_item = this.allocator.Alloc(CPyMarshal.PtrSize);
            CPyMarshal.WritePtr(listStruct.ob_item, itemPtr);
            Marshal.StructureToPtr(listStruct, listPtr, false);
        }
        
        
        private void 
        IC_PyList_Append_NonEmpty(IntPtr listPtr, ref PyListObject listStruct, IntPtr itemPtr)
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
                this.IC_PyList_Append_Empty(listPtr, ref listStruct, itemPtr);
            }
            else
            {
                this.IC_PyList_Append_NonEmpty(listPtr, ref listStruct, itemPtr);
            }
            
            List list = (List)this.Retrieve(listPtr);
            list.append(this.Retrieve(itemPtr));
            this.IncRef(itemPtr);
            return 0;
        }
        
        
        public override int
        PyList_SetItem(IntPtr listPtr, int index, IntPtr itemPtr)
        {
            if (!this.HasPtr(listPtr))
            {
                this.DecRef(itemPtr);
                return -1;
            }
            IntPtr typePtr = CPyMarshal.ReadPtrField(listPtr, typeof(PyObject), "ob_type");
            if (typePtr != this.PyList_Type)
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
            
            if (this.map.HasPtr(listPtr))
            {
                object item = this.Retrieve(itemPtr);
                List list = (List)this.Retrieve(listPtr);
                list[index] = item;
            }      
            return 0;
        }
        
        
        public override IntPtr
        PyList_GetSlice(IntPtr listPtr, int start, int stop)
        {
            try
            {
                List list = (List)this.Retrieve(listPtr);
                List sliced = (List)list[new Slice(start, stop)];
                return this.Store(sliced);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }
            
            
        private void
        ActualiseList(IntPtr ptr)
        {
            if (this.listsBeingActualised.ContainsKey(ptr))
            {
                throw new Exception("Fatal error: Python25Mapper.listsBeingActualised is somehow corrupt");
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
            this.incompleteObjects.Remove(ptr);
            this.map.Associate(ptr, newList);
        }
    }

}
