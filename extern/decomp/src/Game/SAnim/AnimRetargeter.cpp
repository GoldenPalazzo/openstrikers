#include "Game/SAnim/AnimRetargeter.h"

static inline AnimRetarget* GetAnimRetargetWithSignature_ARL(AnimRetargetList* list, const cSAnim* anim)
{
    long offset;
    AnimRetarget* p;
    AnimRetarget* result = NULL;
    offset = (long)result;

    for (long i = list->m_NumAnimRetargets; i > 0; i--)
    {
        p = (AnimRetarget*)((char*)list->m_pAnimRetarget + offset);
        if (anim->m_nHierarchySignature == p->m_TargetHierarchySignature)
        {
            result = p;
            break;
        }
        offset += sizeof(AnimRetarget);
    }

    return result;
}

static inline void* GetChunkData_ARL(nlChunk* chunk)
{
    u32 alignField = chunk->m_ID & 0x7F000000;

    if (((-alignField) | alignField) >> 31)
    {
        alignField = 1u << (alignField >> 24);
        u32 result = (u32)chunk + alignField;
        result = (result + 7) & ~(alignField - 1);
        return (void*)result;
    }

    return (void*)((u8*)chunk + 8);
}

/**
 * Offset/Address/Size: 0x48 | 0x801EFFD8 | size: 0x10C
 */
AnimRetargetList* AnimRetargetList::Initialize(nlChunk* chunkData)
{
    nlChunk* chunk = (nlChunk*)((u8*)chunkData + 8);
    AnimRetargetList* data = (AnimRetargetList*)GetChunkData_ARL(chunk);

    nlChunk* nextChunk = (nlChunk*)((u8*)chunk + chunk->m_Size + 0x10);
    data->m_pAnimRetarget = (AnimRetarget*)GetChunkData_ARL(nextChunk);

    nlChunk* mapChunk;
    s32 off;
    s32 i = 0;
    off = 0;

    while (i < data->m_NumAnimRetargets)
    {
        mapChunk = (nlChunk*)((u8*)nextChunk + nextChunk->m_Size + 8);
        nextChunk = mapChunk;
        signed short* nextMap = (signed short*)GetChunkData_ARL(mapChunk);

        *(signed short**)((u8*)data->m_pAnimRetarget + off + 8) = nextMap;
        off += 0xC;
        i++;
    }

    return data;
}

/**
 * Offset/Address/Size: 0x0 | 0x801EFF90 | size: 0x48
 */
AnimRetarget* AnimRetargetList::GetAnimRetargetWithSignature(const cSAnim* anim)
{
    return GetAnimRetargetWithSignature_ARL(this, anim);
}
