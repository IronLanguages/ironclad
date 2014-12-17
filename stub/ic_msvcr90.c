
#include <io.h>
#include <stdio.h>

// these are here because:
// (1) I can't DllImport from msvcr90.dll (sxs is ignored, apparently)
// (2) this is slightly easier than forwarding to msvcr90

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

// and this lot is copied (with tiny changes) from PC/nt_dl.c, to enable exactly what the following comment describes

#include <Windows.h>

// Windows "Activation Context" work:
// Our .pyd extension modules are generally built without a manifest (ie,
// those included with Python and those built with a default distutils.
// This requires we perform some "activation context" magic when loading our
// extensions.  In summary:
// * As our DLL loads we save the context being used.
// * Before loading our extensions we re-activate our saved context.
// * After extension load is complete we restore the old context.
// As an added complication, this magic only works on XP or later - we simply
// use the existence (or not) of the relevant function pointers from kernel32.
// See bug 4566 (http://python.org/sf/4566) for more details.

typedef BOOL (WINAPI * PFN_GETCURRENTACTCTX)(HANDLE *);
typedef BOOL (WINAPI * PFN_ACTIVATEACTCTX)(HANDLE, ULONG_PTR *);
typedef BOOL (WINAPI * PFN_DEACTIVATEACTCTX)(DWORD, ULONG_PTR);
typedef BOOL (WINAPI * PFN_ADDREFACTCTX)(HANDLE);
typedef BOOL (WINAPI * PFN_RELEASEACTCTX)(HANDLE);

// locals and function pointers for this activation context magic.
static HANDLE PyWin_DLLhActivationContext = NULL; // one day it might be public
static PFN_GETCURRENTACTCTX pfnGetCurrentActCtx = NULL;
static PFN_ACTIVATEACTCTX pfnActivateActCtx = NULL;
static PFN_DEACTIVATEACTCTX pfnDeactivateActCtx = NULL;
static PFN_ADDREFACTCTX pfnAddRefActCtx = NULL;
static PFN_RELEASEACTCTX pfnReleaseActCtx = NULL;

void _LoadActCtxPointers()
{
	HINSTANCE hKernel32 = GetModuleHandleW(L"kernel32.dll");
	if (hKernel32)
		pfnGetCurrentActCtx = (PFN_GETCURRENTACTCTX) GetProcAddress(hKernel32, "GetCurrentActCtx");
	// If we can't load GetCurrentActCtx (ie, pre XP) , don't bother with the rest.
	if (pfnGetCurrentActCtx) {
		pfnActivateActCtx = (PFN_ACTIVATEACTCTX) GetProcAddress(hKernel32, "ActivateActCtx");
		pfnDeactivateActCtx = (PFN_DEACTIVATEACTCTX) GetProcAddress(hKernel32, "DeactivateActCtx");
		pfnAddRefActCtx = (PFN_ADDREFACTCTX) GetProcAddress(hKernel32, "AddRefActCtx");
		pfnReleaseActCtx = (PFN_RELEASEACTCTX) GetProcAddress(hKernel32, "ReleaseActCtx");
	}
}

ULONG_PTR _Py_ActivateActCtx()
{
	ULONG_PTR ret = 0;
	if (PyWin_DLLhActivationContext && pfnActivateActCtx)
		if (!(*pfnActivateActCtx)(PyWin_DLLhActivationContext, &ret)) {
			printf("Python failed to activate the activation context before loading a DLL\n");
			ret = 0; // no promise the failing function didn't change it!
		}
	return ret;
}

void _Py_DeactivateActCtx(ULONG_PTR cookie)
{
	if (cookie && pfnDeactivateActCtx)
		if (!(*pfnDeactivateActCtx)(0, cookie))
			printf("Python failed to de-activate the activation context\n");
}

BOOL	WINAPI	DllMain (HINSTANCE hInst,
						DWORD dw_reason_for_call,
						LPVOID lpReserved)
{
	switch (dw_reason_for_call)
	{
		case DLL_PROCESS_ATTACH:
			// capture our activation context for use when loading extensions.
			_LoadActCtxPointers();
			if (pfnGetCurrentActCtx && pfnAddRefActCtx)
				if ((*pfnGetCurrentActCtx)(&PyWin_DLLhActivationContext))
					if (!(*pfnAddRefActCtx)(PyWin_DLLhActivationContext))
						printf("Python failed to load the default activation context\n");
			break;

		case DLL_PROCESS_DETACH:
			if (pfnReleaseActCtx)
				(*pfnReleaseActCtx)(PyWin_DLLhActivationContext);
			break;
	}
	return TRUE;
}
