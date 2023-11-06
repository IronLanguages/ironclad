#pragma clang attribute push (__declspec(dllexport), apply_to=any(function, variable(is_global)))

void *ExportedSymbol;
void *AnotherExportedSymbol;
void *Alphabetised;

// out of alphabetical order deliberately
int Jazz(void) { return -1; }
int Func(void) { return -1; }
int Funk(void) { return -1; }

#pragma clang attribute pop