#include "Game/SHierarchy.h"
#include "Game/AI/FuzzyDebugger.h"
#include "NL/nlWare.h"
#include "types.h"

/**
 * Offset/Address/Size: 0x354 | 0x801EE340 | size: 0x3E0
 */
cSHierarchy* cSHierarchy::Initialize(nlChunk* pChunk)
{
    pChunk = pChunk->GetFirstChunk();
    cSHierarchy* pRetval = (cSHierarchy*)pChunk->GetData();

    pChunk = pChunk->GetNextChunk();
    pRetval->m_szName = (const char*)pChunk->GetData();

    pChunk = pChunk->GetNextChunk();
    pRetval->m_pNodeID = (u32*)pChunk->GetData();

    pChunk = pChunk->GetNextChunk();
    pRetval->m_pParent = (int*)pChunk->GetData();

    pChunk = pChunk->GetNextChunk();
    pRetval->m_pNumChildren = (int*)pChunk->GetData();

    pChunk = pChunk->GetNextChunk();
    pRetval->m_pChildren = (int**)pChunk->GetData();

    pChunk = pChunk->GetNextChunk();
    pRetval->m_pPushPop = (int*)pChunk->GetData();

    pChunk = pChunk->GetNextChunk();
    int* pChild = (int*)pChunk->GetData();

    for (int i = 0; i < pRetval->m_nNumNodes; i++)
    {
        if (pRetval->m_pNumChildren[i] > 0)
        {
            pRetval->m_pChildren[i] = pChild;
        }
        else
        {
            pRetval->m_pChildren[i] = 0;
        }
        pChild += pRetval->m_pNumChildren[i];
    }

    int nCurrentDepth = 0;
    pRetval->BuildPushPopFlags(0, 0, nCurrentDepth);

    pChunk = pChunk->GetNextChunk();
    pRetval->m_pMirrorTable = (int*)pChunk->GetData();

    pChunk = pChunk->GetNextChunk();
    pRetval->m_pV3TranslationOffset = (nlVector3*)pChunk->GetData();

    pChunk = pChunk->GetNextChunk();
    pRetval->m_pPreserveBoneLength = (u8*)pChunk->GetData();

    return pRetval;
}

/**
 * Offset/Address/Size: 0xD0 | 0x801EE0BC | size: 0x284
 */
void cSHierarchy::BuildPushPopFlags(int nNode, int nParentDepth, int& nCurrentDepth)
{
    int nNumChildren;
    int i;

    if (nParentDepth != nCurrentDepth)
    {
        m_pPushPop[nNode - 1] = nParentDepth - nCurrentDepth;
        nCurrentDepth = nParentDepth;
    }

    nNumChildren = m_pNumChildren[nNode];
    if (nNumChildren != 0)
    {
        m_pPushPop[nNode] = 1;
        nCurrentDepth = nCurrentDepth + 1;
        nParentDepth = nCurrentDepth;

        for (i = 0; i < nNumChildren; i++)
        {
            BuildPushPopFlags(GetChild(nNode, i), nParentDepth, nCurrentDepth);
        }
    }
    else
    {
        m_pPushPop[nNode] = 0;
    }
}

/**
 * Offset/Address/Size: 0xB8 | 0x801EE0A4 | size: 0x18
 */
int cSHierarchy::GetChild(int i, int j) const
{
    nlAssert(i < m_nNumNodes);
    nlAssert(j < m_pNumChildren[i]);
    return m_pChildren[i][j];
}

/**
 * Offset/Address/Size: 0x78 | 0x801EE064 | size: 0x40
 */
int cSHierarchy::GetNodeIndexByID(unsigned int id) const
{
    for (int i = 0; i < m_nNumNodes; i++)
    {
        if (id == m_pNodeID[i])
        {
            return i;
        }
    }
    return -1;
}

/**
 * Offset/Address/Size: 0x68 | 0x801EE054 | size: 0x10
 */
u32 cSHierarchy::GetNodeID(int i) const
{
    nlAssert(i < m_nNumNodes);
    return m_pNodeID[i];
}

/**
 * Offset/Address/Size: 0x58 | 0x801EE044 | size: 0x10
 */
int cSHierarchy::GetNumChildren(int i) const
{
    nlAssert(i < m_nNumNodes);
    return m_pNumChildren[i];
}

/**
 * Offset/Address/Size: 0x48 | 0x801EE034 | size: 0x10
 */
int cSHierarchy::GetMirroredNode(int i) const
{
    nlAssert(i < m_nNumNodes);
    return m_pMirrorTable[i];
}

/**
 * Offset/Address/Size: 0x38 | 0x801EE024 | size: 0x10
 */
int cSHierarchy::GetPushPop(int i) const
{
    nlAssert(i < m_nNumNodes);
    return m_pPushPop[i];
}

/**
 * Offset/Address/Size: 0x28 | 0x801EE014 | size: 0x10
 */
int cSHierarchy::GetParent(int i) const
{
    nlAssert(i < m_nNumNodes);
    return m_pParent[i];
}

/**
 * Offset/Address/Size: 0x18 | 0x801EE004 | size: 0x10
 */
nlVector3& cSHierarchy::GetTranslationOffset(int i) const
{
    nlAssert(i < m_nNumNodes);
    return m_pV3TranslationOffset[i];
}

/**
 * Offset/Address/Size: 0x0 | 0x801EDFEC | size: 0x18
 */
bool cSHierarchy::PreserveBoneLength(int i) const
{
    nlAssert(i < m_nNumNodes);
    return m_pPreserveBoneLength[i];
}

void cSHierarchy::Dump() const
{
    int nStackIndex = -1;
    int i = 0;
    int j;

    nlAssert(m_nNumNodes > 0 && m_pNodeID);

    do
    {
        nlAssert(i < m_nNumNodes);
        if ((j = nStackIndex + 1) != 0)
        {
            do
            {
                nlPrintf("------------------------------");
            } while (--j != 0);
        }
        nlPrintf("0x%08x (%2d)\n", m_pNodeID[i], m_pParent[i]);
        nStackIndex += m_pPushPop[i];
        i++;
    } while (i < m_nNumNodes);
}
