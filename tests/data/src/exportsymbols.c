#include "dllexport.h"

DLLEXPORT void *ExportedSymbol;
DLLEXPORT void *AnotherExportedSymbol;
DLLEXPORT void *Alphabetised;

// out of alphabetical order deliberately
DLLEXPORT int Jazz(void) { return -1; }
DLLEXPORT int Func(void) { return -1; }
DLLEXPORT int Funk(void) { return -1; }
