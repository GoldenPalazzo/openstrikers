#pragma once
#include <cstdio>
#include <limits>
#include <alloca.h>
#include <new> // needed in nlFile.cpp
#define __alloca alloca
#define __fabsf fabsf
#define __fabs fabs
#define __VA_LIST_COMPAT_DEFINED
typedef __builtin_va_list __va_list;
extern "C" int __float_max[];
extern "C" int __float_nan[];
extern "C" int __float_huge[];
typedef FILE _FILE;

#include <cmath>
inline double __frsqrte(double x) {
    return 1.0 / sqrt(x);
}

#include <cstring>
#define __memcpy memcpy
#if defined(_WIN32) || defined(_MSVC_VER)
    #include <string.h>
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

// aurora fixes
#include <dolphin/gx/GXTexture.h>
#include <dolphin/gx/GXManage.h>
#include <dolphin/gx/GXFrameBuffer.h>
#include <dolphin/vi.h>
typedef GXTexObj _GXTexObj;
typedef GXTlutObj _GXTlutObj;
typedef GXRenderModeObj _GXRenderModeObj;
typedef GXTexGenType _GXTexGenType;
typedef GXTexGenSrc _GXTexGenSrc;
typedef GXTevOp _GXTevOp;
typedef GXTevBias _GXTevBias;
typedef GXTevScale _GXTevScale;
typedef GXTevAlphaArg _GXTevAlphaArg;
typedef GXTevRegID _GXTevRegID;
typedef GXCullMode _GXCullMode;
typedef GXBlendFactor _GXBlendFactor;
typedef GXCompare _GXCompare;
typedef GXLightID _GXLightID;
typedef GXTexMtxType _GXTexMtxType;
typedef GXVtxFmt _GXVtxFmt;
typedef GXProjectionType _GXProjectionType;
typedef GXTexFmt _GXTexFmt;
typedef GXPrimitive _GXPrimitive;
typedef GXTlut _GXTlut;
inline void GXClearGPMetric() {}
inline void GXSetGPMetric(int, int) {}
inline void GXReadGPMetric(u32* val0, u32* val1) { *val0 = 0; *val1 = 0; }
inline void GXInitFogAdjTable(void* table, u16 width, float projParam[4][4]) { /* stub */ }
inline GXRenderModeObj GXEurgb60Hz480IntDf = {}; // stub
typedef const float (*CMtxP)[4];
inline void SISetSamplingRate(int) {}
inline void PADSetSamplingCallback(void (*)(void)) {}  // PADSamplingCallback = void (*)(void)

#include <dolphin/mtx.h>
#include <dolphin/mtx/mtx44ext.h>

#ifdef __cplusplus
extern "C" {
#endif
inline void GXWaitDrawDone() {}
// --- Cache / PPC stubs ---
inline void PPCSync() {}
inline void DCFlushRangeNoSync(void*, u32) {}
inline void DCStoreRangeNoSync(void*, u32) {}
inline void DCStoreRange(void*, u32) {}

inline void DCFlushRange(void*, u32) {}
inline void DCZeroRange(void*, u32) {}
inline void DCInvalidateRange(void*, u32) {}


// --- VI stubs ---

inline void VISetBlack(int) {}
inline void VIWaitForRetrace() {}

inline u32 VIGetRetraceCount() { return 0; }
inline void VISetNextFrameBuffer(void*) {}
inline VIRetraceCallback VISetPreRetraceCallback(VIRetraceCallback) {}
inline VIRetraceCallback VISetPostRetraceCallback(VIRetraceCallback cb);
inline u32 VIGetDTVStatus() { return 0; }



// --- OS stubs ---

inline void OSYieldThread() {}
inline u32 OSGetConsoleType() { return 0; }

inline BOOL OSDisableInterrupts() { return 0; }
inline BOOL OSRestoreInterrupts(BOOL) {return 0;}
inline u32 OSGetResetCode() { return 0; }
inline void OSResetSystem(int, u32, BOOL) {}
inline u32 OSGetSoundMode() { return 0; }

inline void OSSetSoundMode(u32) {}
inline u8 OSGetLanguage() { return 0; }
inline u32 OSGetProgressiveMode() { return 0; }

inline void OSSetProgressiveMode(u32) {}
inline u32 OSGetEuRgb60Mode() { return 0; }
inline void OSSetEuRgb60Mode(u32) {}

inline BOOL OSGetResetButtonState() { return 0; }
inline void OSClearStack(u8) {}

// --- GX stubs ---
inline void GXPeekARGB(u16, u16, u32* val) { *val = 0; }

inline void GXPokeColorUpdate(GXBool) {}
inline void GXPokeBlendMode(GXBlendMode, GXBlendFactor, GXBlendFactor, GXLogicOp) {}

inline void GXPokeARGB(u16, u16, u32) {}
inline f32 GXGetYScaleFactor(u16, u16) { return 1.0f; }
extern GXRenderModeObj GXNtsc480Prog; // declaration only, defined in compat_shims.cpp

// --- VM stubs ---

inline void VMInit(uintptr_t baseAddr, size_t initialCommitSize, uintptr_t limitAddr) {}
inline void VMAlloc(uintptr_t address, size_t size) {}
typedef void (*VMLogStatsCallback)(u32 faultAddr, u32 mainAddr, u32 pageIndex, u32 elapsed, u32 wroteBack);
inline void VMSetLogStatsCallback(VMLogStatsCallback cb) {}
#ifdef __cplusplus
}
#endif
