include ../Makefile.config

../build/ironclad/python25.dll: stub.asm.o stub.c.o 
	gcc $(CFLAGS) -shared -o ../build/ironclad/python25.dll stub.asm.o stub.c.o
stub.asm.o: generated
	nasm -o stub.asm.o -f $(OBJ_FORMAT) stub.generated.asm
stub.c.o: generated
	gcc $(CFLAGS) -o stub.c.o -c stubmain.c
generated: *.c
	ipy ../tools/buildstub.py $(PYTHON_DLL) . .
clean:
	$(RM) *.o stub.generated.*
	$(RM) ..\build\ironclad\python25.dll
