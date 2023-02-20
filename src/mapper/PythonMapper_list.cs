using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Operations;
using IronPython.Runtime.Types;

using Ironclad.Structs;


namespace Ironclad
{
    public partial class PythonMapper : PythonApi
    {
        public override void 
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
            dgt_void_ptr freeDgt = CPyMarshal.ReadFunctionPtrField<dgt_void_ptr>(this.PyList_Type, typeof(PyTypeObject), nameof(PyTypeObject.tp_free));
            freeDgt(listPtr);
        }
        
        
        private IntPtr
        StoreTyped(PythonList list)
        {
            int length = list.__len__();
            PyListObject listStruct = new PyListObject();
            listStruct.ob_refcnt = 1;
            listStruct.ob_type = this.PyList_Type;
            listStruct.ob_size = length;
            listStruct.allocated = length;

            nint bytes = length * CPyMarshal.PtrSize;
            IntPtr data = this.allocator.Alloc(bytes);
            listStruct.ob_item = data;
            for (int i = 0; i < length; i++)
            {
                CPyMarshal.WritePtr(data, this.Store(list[i]));
                data = CPyMarshal.Offset(data, CPyMarshal.PtrSize);
            }

            IntPtr listPtr = this.allocator.Alloc(Marshal.SizeOf<PyListObject>());
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

            IntPtr listPtr = this.allocator.Alloc(Marshal.SizeOf<PyListObject>());
            Marshal.StructureToPtr(list, listPtr, false);
            this.map.Associate(listPtr, new PythonList());
            return listPtr;
        }

        public override IntPtr 
        PyList_New(nint length)
        {
            if (length == 0)
            {
                return this.IC_PyList_New_Zero();
            }

            PyListObject list = new PyListObject();
            list.ob_refcnt = 1;
            list.ob_type = this.PyList_Type;
            list.ob_size = length;
            list.allocated = length;
            
            nint bytes = length * CPyMarshal.PtrSize;
            list.ob_item = this.allocator.Alloc(bytes);
            CPyMarshal.Zero(list.ob_item, bytes);
            
            IntPtr listPtr = this.allocator.Alloc(Marshal.SizeOf<PyListObject>());
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
            nint oldAllocated = listStruct.allocated;
            nint oldAllocatedBytes = oldAllocated * CPyMarshal.PtrSize;
            listStruct.ob_size += 1;
            listStruct.allocated += 1;
            IntPtr oldDataStore = listStruct.ob_item;

            nint newAllocatedBytes = listStruct.allocated * CPyMarshal.PtrSize;
            listStruct.ob_item = this.allocator.Realloc(listStruct.ob_item, newAllocatedBytes);
            
            CPyMarshal.WritePtr(CPyMarshal.Offset(listStruct.ob_item, oldAllocatedBytes), itemPtr);
            Marshal.StructureToPtr(listStruct, listPtr, false);
        }
        
        
        public override int 
        PyList_Append(IntPtr listPtr, IntPtr itemPtr)
        {
            PyListObject listStruct = (PyListObject)Marshal.PtrToStructure(listPtr, typeof(PyListObject));
            if (listStruct.ob_type != this.PyList_Type)
            {
                this.LastException = PythonOps.TypeError("PyList_Append: not a list");
                return -1;
            }

            if (listStruct.ob_item == IntPtr.Zero)
            {
                this.IC_PyList_Append_Empty(listPtr, ref listStruct, itemPtr);
            }
            else
            {
                this.IC_PyList_Append_NonEmpty(listPtr, ref listStruct, itemPtr);
            }
            
            PythonList list = (PythonList)this.Retrieve(listPtr);
            list.append(this.Retrieve(itemPtr));
            this.IncRef(itemPtr);
            return 0;
        }
        
        
        public override int
        PyList_SetItem(IntPtr listPtr, nint index, IntPtr itemPtr)
        {
            if (!this.HasPtr(listPtr))
            {
                this.DecRef(itemPtr);
                return -1;
            }
            IntPtr typePtr = CPyMarshal.ReadPtrField(listPtr, typeof(PyObject), nameof(PyObject.ob_type));
            if (typePtr != this.PyList_Type)
            {
                this.DecRef(itemPtr);
                return -1;
            }
            
            nint length = CPyMarshal.ReadPtrField(listPtr, typeof(PyListObject), nameof(PyListObject.ob_size));
            if (index < 0 || index >= length)
            {
                this.DecRef(itemPtr);
                return -1;
            }
            
            IntPtr dataPtr = CPyMarshal.ReadPtrField(listPtr, typeof(PyListObject), nameof(PyListObject.ob_item));
            IntPtr oldItemPtrPtr = CPyMarshal.Offset(dataPtr, (int)(index * CPyMarshal.PtrSize));
            IntPtr oldItemPtr = CPyMarshal.ReadPtr(oldItemPtrPtr);
            if (oldItemPtr != IntPtr.Zero)
            {
                this.DecRef(oldItemPtr);
            }
            CPyMarshal.WritePtr(oldItemPtrPtr, itemPtr);
            
            if (this.map.HasPtr(listPtr))
            {
                object item = this.Retrieve(itemPtr);
                PythonList list = (PythonList)this.Retrieve(listPtr);
                list[checked((int)index)] = item;
            }      
            return 0;
        }
        
        
        public override IntPtr
        PyList_GetSlice(IntPtr listPtr, nint start, nint stop)
        {
            try
            {
                PythonList list = (PythonList)this.Retrieve(listPtr);
                PythonList sliced = (PythonList)list[new Slice(checked((int)start), checked((int)stop))];
                return this.Store(sliced);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }


        public override IntPtr
        PyList_GetItem(IntPtr listPtr, nint idx)
        {
            try
            {
                PythonList list = (PythonList)this.Retrieve(listPtr);
                return this.Store(list[checked((int)idx)]);
            }
            catch (Exception e)
            {
                this.LastException = e;
                return IntPtr.Zero;
            }
        }


        public override IntPtr
        PyList_AsTuple(IntPtr listPtr)
        {
            try
            {
                PythonTuple tuple = new PythonTuple(this.Retrieve(listPtr));
                return this.Store(tuple);
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
                throw new Exception("Fatal error: PythonMapper.listsBeingActualised is somehow corrupt");
            }
            
            PythonList newList = new PythonList();
            this.listsBeingActualised[ptr] = newList;
            
            nint length = CPyMarshal.ReadPtrField(ptr, typeof(PyListObject), nameof(PyListObject.ob_size));
            if (length != 0)
            {
                IntPtr itemPtrPtr = CPyMarshal.ReadPtrField(ptr, typeof(PyListObject), nameof(PyListObject.ob_item));
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
