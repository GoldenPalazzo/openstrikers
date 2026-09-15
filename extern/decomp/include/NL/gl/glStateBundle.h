#ifndef _GLSTATEBUNDLE_H_
#define _GLSTATEBUNDLE_H_

#include "types.h"

#pragma pack(push, 1)
struct glStateBundle
{
    /* 0x00 */ unsigned long long texturestate; // size 0x8
    /* 0x08 */ unsigned long materialstate;     // size 0x4
    /* 0x0C */ unsigned long program;           // size 0x4
    /* 0x10 */ unsigned long raster;            // size 0x4
    /* 0x14 */ unsigned long matrix;            // size 0x4
    /* 0x18 */ unsigned long texture[6];        // size 0x18 (18, 1C, 20, 24, 28, 2C)
    /* 0x30 */ unsigned char texconfig;         // size 0x1
    /* 0x31 */ unsigned char pad;               // size 0x1
    /* 0x32 */ unsigned long userStateKey;      // size 0x4
}; // total size: 0x36

struct gl_StateBitfield
{
    /* 0x00 */ s32 startBit;
    /* 0x04 */ s32 numBits;
}; // total size: 0x8

#pragma pack(pop)

#endif // _GLSTATEBUNDLE_H_
