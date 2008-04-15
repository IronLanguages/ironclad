using System;
using System.Runtime.InteropServices;

using IronPython.Runtime;
using IronPython.Runtime.Types;

using Ironclad.Structs;


namespace Ironclad
{
    public partial class Python25Mapper : PythonMapper
    {
        public override void
        Fill_PyList_Type(IntPtr address)
        {
            IntPtr tp_deallocPtr = CPyMarshal.Offset(
                address, Marshal.OffsetOf(typeof(PyTypeObject), "tp_dealloc"));
            CPyMarshal.WritePtr(tp_deallocPtr, this.GetMethodFP("PyList_Dealloc"));

            IntPtr tp_freePtr = CPyMarshal.Offset(
                address, Marshal.OffsetOf(typeof(PyTypeObject), "tp_free"));
            CPyMarshal.WritePtr(tp_freePtr, this.GetAddress("PyObject_Free"));
            
            this.StoreUnmanagedData(address, TypeCache.List);
        }
        
        
        private IntPtr
        Store(List list)
        {
            IntPtr listPtr = this.PyList_New(0);
            for (int i = 0; i < list.GetLength(); i++)
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
            PyListObject list = new PyListObject();
            list.ob_refcnt = 1;
            list.ob_type = this.PyList_Type;
            list.ob_size = (uint)length;
            list.allocated = (uint)length;
            
            if (length == 0)
            {
                list.ob_item = IntPtr.Zero;
            }
            else
            {
                int bytes = length * CPyMarshal.PtrSize;
                list.ob_item = this.allocator.Alloc(bytes);
                CPyMarshal.Zero(list.ob_item, bytes);
            }
            
            IntPtr listPtr = this.allocator.Alloc(Marshal.SizeOf(typeof(PyListObject)));
            Marshal.StructureToPtr(list, listPtr, false);
            this.StoreUnmanagedData(listPtr, new List());
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
            list.Append(this.Retrieve(itemPtr));
            this.IncRef(itemPtr);
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
        
        
        public virtual void 
        PyList_Dealloc(IntPtr listPtr)
        {
            PyListObject listStruct = (PyListObject)Marshal.PtrToStructure(listPtr, typeof(PyListObject));
            if (listStruct.ob_item != IntPtr.Zero)
            {
                IntPtr itemPtr = listStruct.ob_item;
                for (int i = 0; i < listStruct.ob_size; i++)
                {
                    this.DecRef(CPyMarshal.ReadPtr(itemPtr));
                    itemPtr = CPyMarshal.Offset(itemPtr, CPyMarshal.PtrSize);
                }
                this.allocator.Free(listStruct.ob_item);
            }
            IntPtr freeFPPtr = CPyMarshal.Offset(
                this.PyList_Type, Marshal.OffsetOf(typeof(PyTypeObject), "tp_free"));
            IntPtr freeFP = CPyMarshal.ReadPtr(freeFPPtr);
            PyObject_Free_Delegate freeDgt = (PyObject_Free_Delegate)Marshal.GetDelegateForFunctionPointer(
                freeFP, typeof(PyObject_Free_Delegate));
            freeDgt(listPtr);
        }
        
    }

}
