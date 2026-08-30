#pragma once
#include <limits>
#define __fabsf fabsf
typedef __builtin_va_list __va_list;
extern "C" int __float_max[];

// aurora fixes
#include <dolphin/gx/GXTexture.h>
typedef GXTexObj _GXTexObj;
typedef GXTlutObj _GXTlutObj;
