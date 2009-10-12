# sorry about this -- colons in absolute windows paths confuse target patterns
MINGW_LIB="..\..\..\MinGW\lib"

all:
	echo "please 'make patch' or 'make unpatch'"


patch: libmsvcr90.a $(MINGW_LIB)\libmsvcr90.a.old
	copy libmsvcr90.a $(MINGW_LIB)

libmsvcr90.a: msvcr90.def
	dlltool -D msvcr90.dll -d msvcr90.def -l libmsvcr90.a

msvcr90.def: C:\Windows\winsxs\x86_microsoft.vc90.crt_1fc8b3b9a1e18e3b_9.0.21022.8_none_bcb86ed6ac711f91\msvcr90.dll
	pexports C:\Windows\winsxs\x86_microsoft.vc90.crt_1fc8b3b9a1e18e3b_9.0.21022.8_none_bcb86ed6ac711f91\msvcr90.dll > msvcr90.def

$(MINGW_LIB)\libmsvcr90.a.old:
	move $(MINGW_LIB)\libmsvcr90.a $(MINGW_LIB)\libmsvcr90.a.old


unpatch:
	move $(MINGW_LIB)\libmsvcr90.a.old $(MINGW_LIB)\libmsvcr90.a
