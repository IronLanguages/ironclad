#pragma clang attribute push (__declspec(dllexport), apply_to=any(function, variable(is_global)))

int value = 1;

void PyInit_setvalue(void)
{
	value = 2;
}

#pragma clang attribute pop