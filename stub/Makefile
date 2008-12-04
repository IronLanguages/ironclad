include ../Makefile.config

../build/python25.dll: stub.asm.o stub.c.o
	gcc $(CFLAGS) -shared -o ../build/python25.dll stub.asm.o stub.c.o
stub.asm.o: generated
	nasm -o stub.asm.o -f $(OBJ_FORMAT) stub.generated.asm
stub.c.o: generated
	gcc $(CFLAGS) -o stub.c.o -c stubmain.c
generated: stubmain.c PyAPI_DATAs.c PyAPI_FUNCs.c PyAPI_types.c abstract.c getargs.c modsupport.c stringobject.c ceval.c mysnprintf.c
	ipy ../tools/buildstub.py $(PYTHON_DLL) . .
clean:
	del *.o stub.generated.*
	del ..\build\python25.dll
