python tools\buildstub.py C:/WINDOWS/system32/python25.dll build 
csc /out:build\jumpy.dll /t:library /r:ironpython\IronPython.dll /r:ironpython\IronMath.dll /nologo src\*.cs 
call runtests.bat
