../build/python25.dll: stub.asm.o stub.c.o
	gcc -shared -o ../build/python25.dll stub.asm.o stub.c.o
stub.asm.o: generated
	nasm -o stub.asm.o -f win32 stub.generated.asm
stub.c.o: generated
	gcc -o stub.c.o -c stubmain.c
generated: stubmain.c PyAPI_DATAs.c PyAPI_FUNCs.c PyAPI_types.c abstract.c getargs.c modsupport.c stringobject.c ceval.c mysnprintf.c
	ipy ../tools/buildstub.py C:/WINDOWS/system32/python25.dll . .
