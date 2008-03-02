../build/python25.dll: asm.o c.o
	gcc -shared -o ../build/python25.dll asm.o c.o
asm.o: generated
	nasm -o asm.o -f win32 generated.asm
c.o: generated
	gcc -o c.o -c python25.c
generated: python25.c PyAPI_DATAs.c PyAPI_FUNCs.c PyAPI_types.c abstract.c getargs.c modsupport.c
	ipy ../tools/buildstub.py C:/WINDOWS/system32/Python25.dll . .
