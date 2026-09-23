#include "NL/gl/glUserData.h"
#include "NL/gl/glMemory.h"
#include "NL/nlString.h"
#include <string.h>

/**
 * Offset/Address/Size: 0x0 | 0x801DEB78 | size: 0x2C
 */
// One pointer-sized slot per eGLUserData type: needs to scale with uintptr_t 
static constexpr size_t kUserDataBlockSize = GLUD_Num * sizeof(uintptr_t);

bool glUserHasType(eGLUserData type, const glModelPacket* pPacket)
{
    uintptr_t* userdata = (uintptr_t*)(pPacket->userData);
    if (userdata == NULL)
    {
        return false;
    }

    uintptr_t val = userdata[(int)type];
    return (val != 0) ? true : false;
}

/**
 * Offset/Address/Size: 0x2C | 0x801DEBA4 | size: 0x14
 */
void glUserDetach(eGLUserData type, glModelPacket* pPacket)
{
    uintptr_t* userdata = (uintptr_t*)(pPacket->userData);
    userdata[(int)type] = 0;
}

/**
 * Offset/Address/Size: 0x40 | 0x801DEBB8 | size: 0x88
 */
void glUserDup(glModelPacket* pDest, const glModelPacket* pSrc, bool bPerm)
{
    if (pSrc->userData != 0)
    {
        void* copyBlock;
        if (bPerm)
        {
            copyBlock = glResourceAlloc(kUserDataBlockSize, GLM_Header);
        }
        else
        {
            copyBlock = glFrameAlloc(kUserDataBlockSize, GLM_Header);
        }

        memcpy(copyBlock, (uintptr_t*)pSrc->userData, kUserDataBlockSize);
        pDest->userData = (uintptr_t)copyBlock;
    }
}

/**
 * Offset/Address/Size: 0xC8 | 0x801DEC40 | size: 0x94
 */
void glUserAttach(const void* pUserData, glModelPacket* pPacket, bool bPerm)
{
    if ((uintptr_t*)pPacket->userData == NULL)
    {
        void* block;
        if (bPerm)
        {
            block = glResourceAlloc(kUserDataBlockSize, GLM_Header);
        }
        else
        {
            block = glFrameAlloc(kUserDataBlockSize, GLM_Header);
        }

        nlZeroMemory(block, kUserDataBlockSize);
        pPacket->userData = (uintptr_t)block;
    }

    eGLUserData type = *(eGLUserData*)pUserData;
    ((uintptr_t*)(pPacket->userData))[(int)type] = (uintptr_t)pUserData;
}

/**
 * Offset/Address/Size: 0x15C | 0x801DECD4 | size: 0x8
 */
void* glUserGetData(const void* pUserData)
{
    return (u8*)pUserData + 4;
}

/**
 * Offset/Address/Size: 0x164 | 0x801DECDC | size: 0x58
 */
void* glUserAlloc(eGLUserData type, unsigned long size, bool bPerm)
{
    unsigned long actualSize = size + 4;
    void* mem;

    if (bPerm)
    {
        mem = glResourceAlloc(actualSize, GLM_Header);
    }
    else
    {
        mem = glFrameAlloc(actualSize, GLM_Header);
    }

    if (mem == 0)
    {
        return mem;
    }

    *(u32*)mem = (u32)type;
    return mem;
}
