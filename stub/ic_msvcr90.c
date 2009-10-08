
#include <io.h>
#include <stdio.h>

// these are here because:
// (1) I can't DllImport from msvcr90.dll (sxs is ignored, apparently)
// (2) this is slightly easier than forwarding to msvcr90, because there's no messing around with .defs and foo@4s

FILE* IC__fdopen(int fd, const char *mode)
{
    return _fdopen(fd, mode);
}

int IC__open_osfhandle(intptr_t f, int flags)
{
    return _open_osfhandle(f, flags);
}

size_t IC_fread(void *buf, size_t size, size_t count, FILE *file)
{
    return fread(buf, size, count, file);
}

size_t IC_fwrite(void *buf, size_t size, size_t count, FILE *file)
{
    return fwrite(buf, size, count, file);
}

int IC_fflush(FILE *file)
{
    return fflush(file);
}

int IC_fclose(FILE *file)
{
    return fclose(file);
}
