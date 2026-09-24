#ifndef _SANIM_H_
#define _SANIM_H_

#include "types.h"

#include "NL/nlMath.h"
#ifdef TARGET_PC
#include "port/endian.hpp"
#endif

class cPoseAccumulator;

struct PackedScale
{
#ifndef TARGET_PC
    signed short x; // offset 0x0, size 0x2
    signed short y; // offset 0x2, size 0x2
    signed short z; // offset 0x4, size 0x2
#else
    port::be<s16> x; // offset 0x0, size 0x2
    port::be<s16> y; // offset 0x2, size 0x2
    port::be<s16> z; // offset 0x4, size 0x2
#endif
}; // total size: 0x6

struct PackedTrans
{
#ifndef TARGET_PC
    float x; // offset 0x0, size 0x4
    float y; // offset 0x4, size 0x4
    float z; // offset 0x8, size 0x4
#else
    port::be<f32> x; // offset 0x0, size 0x4
    port::be<f32> y; // offset 0x4, size 0x4
    port::be<f32> z; // offset 0x8, size 0x4
#endif
}; // total size: 0xC

enum ePlayMode
{
    PM_CYCLIC = 0,
    PM_HOLD = 1,
};

// This object should be externally allocated at runtime with nlMallocs, so
// no swap should be necessary
class cSAnimCallback
{
public:
    /* 0x0 */ float m_fTime;
#ifndef TARGET_PC
    /* 0x4 */ unsigned int m_nParam1;
    /* 0x8 */ void (*m_funcCallback)(unsigned int);
#else
    /* 0x4 */ uintptr_t m_nParam1;
    /* 0x8 */ void (*m_funcCallback)(uintptr_t);
#endif
    /* 0xC */ cSAnimCallback* next;
}; // total size: 0x10

class nlChunk
{
public:
    nlChunk* GetNextChunk();
    u32 GetSize();
    u32 GetID();
    nlChunk* GetLastChunk();
    nlChunk* GetFirstChunk();
    u8 IsNestedChunk();
    void* GetData();
    void* GetUnalignedData();
    void* GetAlignedData();
    u32 GetChunkAlignment();
    bool IsAlignedChunk();

#ifndef TARGET_PC
    /* 0x00 */ u32 m_ID;
    /* 0x04 */ u32 m_Size;
#else
    /* 0x00 */ port::be<u32> m_ID;
    /* 0x04 */ port::be<u32> m_Size;
#endif
}; // size: 0x8

inline nlChunk* nlChunk::GetNextChunk()
{
    return (nlChunk*)((u8*)this + GetSize() + sizeof(nlChunk));
}

inline u32 nlChunk::GetSize()
{
    return m_Size;
}

inline u32 nlChunk::GetID()
{
    return m_ID & 0x80FFFFFF;
}

inline nlChunk* nlChunk::GetLastChunk()
{
    return (nlChunk*)((u8*)this + GetSize() + sizeof(nlChunk));
}

inline nlChunk* nlChunk::GetFirstChunk()
{
    return (nlChunk*)((u8*)this + sizeof(nlChunk));
}

inline u8 nlChunk::IsNestedChunk()
{
    return (m_ID & 0x80000000) != 0;
}

inline void* nlChunk::GetData()
{
    bool isAligned = IsAlignedChunk();
    if (isAligned)
    {
        return GetAlignedData();
    }
    return GetUnalignedData();
}

inline void* nlChunk::GetUnalignedData()
{
    return this + 1;
}

inline void* nlChunk::GetAlignedData()
{
    u32 alignment = 1u << (GetChunkAlignment() >> 24);
#ifndef TARGET_PC
    return (void*)nlAlignUp((unsigned int)GetUnalignedData(), alignment);
#else
    return (void*)nlAlignUp((uintptr_t)GetUnalignedData(), (uintptr_t)alignment);
#endif
}

inline u32 nlChunk::GetChunkAlignment()
{
    return m_ID & 0x7F000000;
}

inline bool nlChunk::IsAlignedChunk()
{
    return GetChunkAlignment();
}

class cIdentifier
{
public:
    unsigned int GetHashID() const
    {
        return m_uHashID;
    }

    void Destroy()
    {
    }

protected:
#ifndef TARGET_PC
    /* 0x0 */ const char* m_szName;
    /* 0x4 */ unsigned int m_uHashID;
#else
    /* 0x0 */ port::SelfRelPtr32<const char> m_szName;
    /* 0x4 */ port::be<u32> m_uHashID;
#endif
}; // total size: 0x8

class cSAnim : public cIdentifier
{
public:
    typedef char* MemType;

    static cSAnim* Initialize(nlChunk* pChunk);
    static u8 IsValidChunkID(u32 id)
    {
        return (id & 0x80FFFFFF) == 0x80017000;
    }

    void BlendRot(int nodeIndex, int remappedNodeIndex, float tNorm, float weight, cPoseAccumulator* acc, bool additive) const;
    void BlendScale(int nodeIndex, int remappedNodeIndex, float tNorm, float weight, cPoseAccumulator* acc, bool additive) const;
    void BlendTrans(int nAccumulatorNode, int nSAnimNode, float fTime, float fWeight, cPoseAccumulator* pAccumulator, bool bMirror) const;
    void Destroy();
    void GetRootRot(float fTime, unsigned short* pRootRot) const;
    void GetRootTrans(float t, nlVector3* out) const;
#ifndef TARGET_PC
    void CreateCallback(float fTime, unsigned int nParam1, void (*funcCallback)(unsigned int));
#else
    void CreateCallback(float fTime, uintptr_t nParam1, void (*funcCallback)(uintptr_t));
#endif
    float GetMorphWeight(int channel, float fTime) const;

    cSAnimCallback* GetCallbackList() const
    {
        return m_pCallbackList;
    }

    float GetDuration() const
    {
        return (float)m_nNumKeys / 30.0f;
    }

#ifndef TARGET_PC
    /* 0x08 */ unsigned int m_nNumKeys;
    /* 0x0C */ unsigned int m_nNumNodes;
    /* 0x10 */ unsigned int m_nNumMorphChannels;
    /* 0x14 */ const unsigned int* m_pNodeProperties;
    /* 0x18 */ void* m_pRotKeys;
    /* 0x1C */ PackedScale** m_pScaleKeys;
    /* 0x20 */ PackedTrans** m_pTransKeys;
    /* 0x24 */ unsigned int m_nNumRootKeys;
    /* 0x28 */ unsigned short* m_pRootRot;
    /* 0x2C */ nlVector3* m_pRootTrans;
    /* 0x30 */ unsigned long* m_nMorphIds;
    /* 0x34 */ const unsigned int* m_pNumMorphKeys;
    /* 0x38 */ unsigned char* m_pMorphKeys;
    /* 0x3C */ cSAnimCallback* m_pCallbackList;
    /* 0x40 */ float m_fLinearSpeed;
    /* 0x44 */ unsigned long m_nHierarchySignature;
#else
    /* 0x08 */ port::be<u32> m_nNumKeys;
    /* 0x0C */ port::be<u32> m_nNumNodes;
    /* 0x10 */ port::be<u32> m_nNumMorphChannels;
    /* 0x14 */ port::SelfRelPtr32<const port::be<u32>> m_pNodeProperties;
    /* 0x18 */ port::SelfRelPtr32<port::SelfRelPtr32<void>> m_pRotKeys;
    /* 0x1C */ port::SelfRelPtr32<port::SelfRelPtr32<PackedScale>> m_pScaleKeys;
    /* 0x20 */ port::SelfRelPtr32<port::SelfRelPtr32<PackedTrans>> m_pTransKeys;
    /* 0x24 */ port::be<u32> m_nNumRootKeys;
    /* 0x28 */ port::SelfRelPtr32<port::be<u16>> m_pRootRot;
    /* 0x2C */ port::SelfRelPtr32<nlVector3> m_pRootTrans;
    /* 0x30 */ port::SelfRelPtr32<const port::be<u32>> m_nMorphIds;
    /* 0x34 */ port::SelfRelPtr32<const port::be<u32>> m_pNumMorphKeys;
    /* 0x38 */ port::SelfRelPtr32<const u8> m_pMorphKeys;
    /* 0x3C */ port::SelfRelPtr32<cSAnimCallback> m_pCallbackList;
    /* 0x40 */ float m_fLinearSpeed;
    /* 0x44 */ port::be<u32> m_nHierarchySignature;
#endif
}; // total size: 0x48

#endif // _SANIM_H_
