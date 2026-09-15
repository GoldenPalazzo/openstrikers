#ifndef _GLXDISPLAYLIST_H_
#define _GLXDISPLAYLIST_H_

#include "NL/gl/glUserData.h"

struct DisplayList
{
    /* 0x00 */ u32 magic;
    /* 0x04 */ void* list;
    /* 0x08 */ u32 size;
    /* 0x0C */ unsigned short* indices;
}; // total size: 0x10

DisplayList* dlMakeDisplayList(const glModelPacket* packet, bool permanent);
u32 dlGetSize(unsigned long addr);
void* dlGetDisplayList(unsigned long addr);
bool dlIsDisplayList(unsigned long addr);
DisplayList* dlGetStruct(unsigned long addr);

#endif // _GLXDISPLAYLIST_H_
