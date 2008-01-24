python tools\buildstub.py C:\WINDOWS\system32\python25.dll build
csc /out:build\jumpy.dll /t:library src\*.cs
call runtests
