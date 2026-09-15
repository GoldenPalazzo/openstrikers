// Include order is load-bearing; do not sort these lines. MWCC emits one .text
// section per code-contributing header, ordered by parse position, and this TU
// reproduces the original's four blocks (config/G4QE01/splits.txt):
//
//   0x664  MemAlloc.cpp   the seven MemoryAllocator/Callback functions
//   0x054  nlWare.h       weak nlPrintf; discarded at link (AnimInventory.cpp
//                         owns the surviving copy at 0x8000749C), which is why
//                         the split target records this block as zero-length
//   0x148  nlDLRing.h     nlWalkDLRing<> instantiations + nlDLRing* helpers
//   0x0c0  nlRing.h       nlWalkRing<> instantiations
//
// Parsing nlDLRing.h after MemAlloc.h splits its 0x148 block in two and reverses
// the halves, which reorders the .text contribution and breaks the DOL SHA1 --
// while objdiff and the per-unit report both still report 100%.
#include "NL/nlWare.h"
#include "NL/nlDebug.h"
#include "NL/nlDLRing.h"
#include "NL/MemAlloc.h"

// Built with `-inline deferred`: MWCC emits .text in REVERSE source order, so the
// functions below are declared last-to-first relative to their addresses. Parse-time
// .data (the ptmf constants) still follows source order, which is what pins
// TotalFreeMemCallback's ptmf ahead of LargestFreeBlockCallback's.

/**
 * Offset/Address/Size: 0x534 | 0x801CDC80 | size: 0x130
 */
void MemoryAllocator::Free(void* p)
{
    free(p);
}

/**
 * Offset/Address/Size: 0x1D8 | 0x801CD924 | size: 0x35C
 */
void* MemoryAllocator::Allocate(unsigned long size, unsigned int alignment, bool fromEnd)
{
    (void)fromEnd;
    if (alignment <= alignof(max_align_t))
        return malloc(size);

    void* ptr = nullptr;
    unsigned int reqAlign = alignment < sizeof(void*) ? sizeof(void*) : alignment;
    if (posix_memalign(&ptr, reqAlign, size) != 0)
        return nullptr;
    return ptr;
}

/**
 * Offset/Address/Size: 0xE0 | 0x801CD82C | size: 0xF8
 */
void MemoryAllocator::Initialize(void* memory, unsigned int size) {}

class TotalFreeMemCallback
{
public:
    /**
     * Offset/Address/Size: 0xCC | 0x801CD818 | size: 0x14
     */
    void Callback(FreeBlockList* block)
    {
        size = size + block->m_size;
    }

    /* 0x0 */ u32 size;
};

/**
 * Offset/Address/Size: 0x74 | 0x801CD7C0 | size: 0x58
 */
unsigned int MemoryAllocator::TotalFreeMemory()
{
    return 0xffffffff;
}

class LargestFreeBlockCallback
{
public:
    /**
     * Offset/Address/Size: 0x58 | 0x801CD7A4 | size: 0x1C
     */
    void Callback(FreeBlockList* block)
    {
        u32 blockSize;
        u32 maxSize;

        maxSize = largest;
        blockSize = block->m_size;
        if (blockSize >= maxSize)
        {
            maxSize = blockSize;
        }
        largest = maxSize;
    }

    /* 0x0 */ u32 largest;
};

/**
 * Offset/Address/Size: 0x0 | 0x801CD74C | size: 0x58
 */
unsigned int MemoryAllocator::LargestFreeBlock()
{
    return 0xffffffff;
}
