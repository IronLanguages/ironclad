include ../Makefile.config

ifeq ($(OS),windows)
	CFLAGS += -specs=use-msvcr71.spec
endif

../build/ironclad/python25.dll: stub.asm.o stub.c.o 
	gcc $(CFLAGS) -export-all-symbols -shared -o ../build/ironclad/python25.dll stub.asm.o stub.c.o
stub.asm.o: generated
	nasm -o stub.asm.o -f $(OBJ_FORMAT) stub.generated.asm
stub.c.o: generated
	gcc $(CFLAGS) -o stub.c.o -c stubmain.c -I Include
generated: *.c
	ipy ../tools/buildstub.py $(PYTHON_DLL) . .
clean:
	$(RM) *.o stub.generated.*
	$(RM) ..\build\ironclad\python25.dll
