include ../../../Makefile.config

all : ../testutils.dll ../setvalue.pyd ../exportsymbols.dll

../testutils.dll : unmanaged.cs ../../../ironpython/*.dll
	$(CSC) /out:../testutils.dll /t:library /nologo /r:../../../ironpython/Microsoft.Scripting.dll /r:../../../ironpython/Microsoft.Scripting.Core.dll /r:../../../ironpython/IronPython.dll unmanaged.cs

../setvalue.pyd : setvalue.o
	gcc $(CFLAGS) -shared -o ../setvalue.pyd setvalue.o

setvalue.o : setvalue.c
	gcc $(CFLAGS) -o setvalue.o -c setvalue.c

../exportsymbols.dll : exportsymbols.o
	gcc $(CFLAGS) -shared -o ../exportsymbols.dll exportsymbols.o

exportsymbols.o : exportsymbols.c
	gcc $(CFLAGS) -o exportsymbols.o -c exportsymbols.c

clean :
	$(RM) *.o
	$(RM) ..\testutils.dll
	$(RM) ..\setvalue.pyd
	$(RM) ..\exportsymbols.dll