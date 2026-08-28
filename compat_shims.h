#include <limits>
#define __fabsf fabsf
typedef __builtin_va_list __va_list;
inline float __get_float_max() { return std::numeric_limits<float>::max(); }

// aurora fixes
#include <dolphin/gx/GXTexture.h>
typedef GXTexObj _GXTexObj;
typedef GXTlutObj _GXTlutObj;
