python tools\buildstub.py C:/WINDOWS/system32/python25.dll build overrides
csc /out:build\jumpy.dll /t:library /r:ironpython\IronPython.dll /r:ironpython\IronMath.dll /nologo src\*.cs 

gcc -o tests/data/setvalue.o -c tests/data/src/setvalue.c
gcc -shared -o tests/data/setvalue.pyd tests/data/setvalue.o
gcc -o tests/data/exportsymbols.o -c tests/data/src/exportsymbols.c
gcc -shared -o tests/data/exportsymbols.dll tests/data/exportsymbols.o
csc /out:tests\data\jumpytestutils.dll /t:library /nologo tests\data\src\PythonStubHarness.cs

call runtests.bat
