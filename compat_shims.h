#pragma once
#include <cstdio>
#include <limits>
#define __fabsf fabsf
#define __fabs fabs
typedef __builtin_va_list __va_list;
extern "C" int __float_max[];
typedef FILE _FILE;

#include <cstring>

// aurora fixes
#include <dolphin/gx/GXTexture.h>
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
