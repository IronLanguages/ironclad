#include "dllexport.h"

DLLEXPORT int value = 1;

DLLEXPORT void PyInit_setvalue(void)
{
	value = 2;
}
