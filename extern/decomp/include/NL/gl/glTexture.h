#ifndef _GLTEXTURE_H_
#define _GLTEXTURE_H_

#include "types.h"

void glTextureReplace(unsigned long texture, const void* buffer, unsigned long length);
void glTextureAdd(unsigned long texture, const void* buffer, unsigned long length);
int glTextureGetNumBits(int component);
u32 glTextureGetHeight();
u32 glTextureGetWidth();
bool glTextureLoad(unsigned long texture);

#endif // _GLTEXTURE_H_
