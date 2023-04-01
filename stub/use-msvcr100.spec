*msvcrt:
msvcr100

*msvcrt_version:
-D__MSVCRT_VERSION__=0x1000

*moldname:
moldname

*cpp:
%(msvcrt_version) %{posix:-D_POSIX_SOURCE} %{mthreads:-D_MT}

*libgcc:
%{mthreads:-lmingwthrd} -lmingw32 -lgcc -l%(moldname) -lmingwex -l%(msvcrt)

