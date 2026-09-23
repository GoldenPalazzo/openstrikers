#ifndef _SHIERARCHY_H_
#define _SHIERARCHY_H_

#include "types.h"
#include "NL/nlMath.h"
#include "Game/SAnim.h"

class nlChunk;

class cSHierarchy : public cIdentifier
{
public:
    typedef char* MemType;

    void Dump() const;
    bool PreserveBoneLength(int i) const;
    nlVector3& GetTranslationOffset(int i) const;
    int GetParent(int i) const;
    int GetPushPop(int i) const;
    int GetMirroredNode(int i) const;
    int GetNumChildren(int i) const;
    u32 GetNodeID(int i) const;
    int GetNodeIndexByID(unsigned int id) const;
    int GetChild(int i, int j) const;
    void BuildPushPopFlags(int nNode, int nParentDepth, int& nCurrentDepth);
    static cSHierarchy* Initialize(nlChunk* pChunk);
    static bool IsValidChunkID(u32 id)
    {
        return (id & 0x80FFFFFF) == 0x80018000;
    }
    inline int GetNumNodes() const { return m_nNumNodes; }
    inline int GetPelvisNodeIndex() const { return m_nPelvisNodeIndex; }
    inline int GetSpineNodeIndex() const { return m_nSpineNodeIndex; }
#ifndef TARGET_PC
    /* 0x08 */ int m_nNumNodes;
    /* 0x0C */ u32* m_pNodeID;
    /* 0x10 */ int* m_pParent;
    /* 0x14 */ int* m_pNumChildren;
    /* 0x18 */ int** m_pChildren;
    /* 0x1C */ int* m_pPushPop;
    /* 0x20 */ int* m_pMirrorTable;
    /* 0x24 */ int m_nPelvisNodeIndex;
    /* 0x28 */ int m_nSpineNodeIndex;
    /* 0x2C */ nlVector3* m_pV3TranslationOffset;
    /* 0x30 */ u8* m_pPreserveBoneLength;
#else
    /* 0x08 */ port::be<int> m_nNumNodes;
    /* 0x0C */ port::SelfRelPtr32<const port::be<u32>> m_pNodeID;
    /* 0x10 */ port::SelfRelPtr32<const port::be<int>> m_pParent;
    /* 0x14 */ port::SelfRelPtr32<const port::be<int>> m_pNumChildren;
    /* 0x18 */ port::SelfRelPtr32<port::SelfRelPtr32<port::be<int>>> m_pChildren;
    /* 0x1C */ port::SelfRelPtr32<int> m_pPushPop; // runtime-computed by BuildPushPopFlags, host-native, no swap needed
    /* 0x20 */ port::SelfRelPtr32<const port::be<int>> m_pMirrorTable;
    /* 0x24 */ port::be<int> m_nPelvisNodeIndex;
    /* 0x28 */ port::be<int> m_nSpineNodeIndex;
    /* 0x2C */ port::SelfRelPtr32<nlVector3> m_pV3TranslationOffset;
    /* 0x30 */ port::SelfRelPtr32<const u8> m_pPreserveBoneLength;
#endif
};

#endif // _SHIERARCHY_H_
