#ifndef _MSL_STRTOLD_H
#define _MSL_STRTOLD_H

#include "types.h"

#ifdef __cplusplus
extern "C" {
#endif // ifdef __cplusplus

f128 __strtold(int max_width, int (*ReadProc)(void*, int, int), void* ReadProcArg, int* chars_scanned, int* overflow);
f64 atof(const char* str);

#ifdef __cplusplus
};
#endif // ifdef __cplusplus

#endif
