#pragma once
#include <stdio.h>
#include <limits.h>
#include <alloca.h>
#ifdef __cpluplus
#include <new> // needed in nlFile.cpp
#endif

#define __alloca alloca
#define __fabsf fabsf
#define __fabs fabs
#define __VA_LIST_COMPAT_DEFINED
typedef __builtin_va_list __va_list;

#ifdef __cplusplus
extern "C" {
#endif
extern int __float_max[];
extern float __float_min[];
extern int __float_nan[];
extern int __float_huge[];
#ifdef __cplusplus
}
#endif

typedef FILE _FILE;

#include <math.h>
static inline double __frsqrte(double x) {
    return 1.0 / sqrt(x);
}

#include <string.h>
#define __memcpy memcpy
#if defined(_WIN32) || defined(_MSVC_VER)
    #ifndef strcmpi
    #define strcmpi _stricmp
    #endif
#else
    #include <strings.h>
    #ifndef strcmpi
    #define strcmpi strcasecmp
    #endif
#endif

#ifndef __cntlzw
#if defined(__GNUC__) || defined(__clang__)
#define __cntlzw(x) ((x) ? __builtin_clz(x) : 32)
#else
// Generic fallback
static inline int __cntlzw(unsigned int val) {
    if (val == 0) return 32;
    int reg = 0;
    if (!(val & 0xFFFF0000)) { reg += 16; val <<= 16; }
    if (!(val & 0xFF000000)) { reg += 8;  val <<= 8;  }
    if (!(val & 0xF0000000)) { reg += 4;  val <<= 4;  }
    if (!(val & 0xC0000000)) { reg += 2;  val <<= 2;  }
    if (!(val & 0x80000000)) { reg += 1; }
    return reg;
}
#endif
#endif

#ifdef __cplusplus
// __construct_new_array: calls constructor for each element

extern "C" inline void* __construct_new_array(void* block, void* ctor, void* dtor, size_t size, size_t n) {
    if (block && ctor) {
        // Cast a puntatore a funzione CodeWarrior: void (*)(void*, int)
        auto ctor_fn = reinterpret_cast<void(*)(void*, int)>(ctor);
        char* p = static_cast<char*>(block);
        for (size_t i = 0; i < n; ++i) {
            ctor_fn(p, 1);
            p += size;
        }
    }
    return block;
}

// __cvt_fp2unsigned: float to unsigned int (truncate toward zero)

extern "C" inline unsigned int __cvt_fp2unsigned(double d) {
    return static_cast<unsigned int>(d);
}

extern "C" unsigned char __ctype_map[];
#endif


