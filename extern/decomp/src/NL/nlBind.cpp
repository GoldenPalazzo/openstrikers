#include "NL/nlBind.h"

#ifdef TARGET_PC
__attribute__((section(".sdata2"))) Placeholder<0> placeholder0 = { };
#else
__declspec(section ".sdata2") Placeholder<0> placeholder0 = { };
#endif
