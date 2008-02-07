all : ../jumpytestutils.dll ../setvalue.pyd ../exportsymbols.dll

../jumpytestutils.dll : PythonStubHarness.cs
	csc /out:../jumpytestutils.dll /t:library /nologo PythonStubHarness.cs

../setvalue.pyd : setvalue.o
	gcc -shared -o ../setvalue.pyd setvalue.o

setvalue.o : setvalue.c
	gcc -o setvalue.o -c setvalue.c

../exportsymbols.dll : exportsymbols.o
	gcc -shared -o ../exportsymbols.dll exportsymbols.o

exportsymbols.o : exportsymbols.c
	gcc -o exportsymbols.o -c exportsymbols.c