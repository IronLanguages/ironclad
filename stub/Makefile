include ../Makefile.config

../build/ironclad/python25.dll: stub.asm.o stub.c.o 
	gcc $(CFLAGS) -shared -o ../build/ironclad/python25.dll stub.asm.o stub.c.o
stub.asm.o: generated
	nasm -o stub.asm.o -f $(OBJ_FORMAT) stub.generated.asm
stub.c.o: generated
	gcc $(CFLAGS) -o stub.c.o -c stubmain.c
generated: stubmain.c PyAPI_DATAs.c PyAPI_FUNCs.c PyAPI_types.c *.c
	ipy ../tools/buildstub.py $(PYTHON_DLL) . .
clean:
	$(RM) *.o stub.generated.*
	$(RM) ..\build\ironclad\python25.dll
cil:
	cp $(CIL_FILE) cil.tar
	tar -xzvf cil.tar
	$(RM) cil.tar
python:
	cp $(PYTHON_FILE) python.tar
	tar -xzvf python.tar
	mv Python-2.* python
	$(RM) python.tar

cilly.bat: cil/Makefile
	cd cil && make cilly;
	$(RM) cilly.bat;
	cp cil/bin/cilly.bat .;

cil/Makefile:
	cd cil && ./configure EXTRASRCDIRS=.. EXTRAFEATURES=prunedefs;
