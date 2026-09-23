#include "NL/nlMemory.h"
#include "NL/MemAlloc.h"
#ifdef TARGET_PC
#include "NL/nlWare.h"
#include "NL/nlDebug.h"
#endif

#include <types.h>

#include "dolphin/os.h"
#ifdef TARGET_PC
#include "dolphin/os/OSAlloc.h"
#endif
#include "dolphin/pad.h"
#include "dolphin/dvd.h"
#include "dolphin/vm/VM.h"
#include "dolphin/vi/vifuncs.h"

static u8 s_MemoryInitialized = 0;
#ifdef TARGET_PC
extern bool g_EngineArenaReady;
#endif

MemoryAllocator StandardAllocator;
MemoryAllocator VirtualAllocator;

#ifdef TARGET_PC
static const void* g_standardBase;
static size_t g_standardSize;
static constexpr size_t g_virtualSize = 0x900000;
// Carved out of the same MEM1 block as g_standardBase (see
// InitializeStandardAndVirtualAllocators) rather than a separate static
// buffer, so that any pointer in Standard and any pointer in Virtual are
// guaranteed to be within g_standardSize + g_virtualSize (< 2GB) of each
// other. This lets port::SelfRelPtr32 relate objects across the two arenas
// safely on 64-bit hosts, where an independent .bss array and a
// calloc/mmap'd heap block have no such guarantee.
static const void* g_virtualBase;

#include <mutex>
// Guards nlInitMemory()'s init sequence below. Must be recursive:
// DVDInit/VIInit/PADInit run *inside* the guarded block on the initializing
// thread and may themselves allocate, re-entering nlInitMemory() on that same
// thread before the lock is released. A plain mutex would deadlock there; a
// std::once_flag can't be made reentrant at all. Being recursive also gives
// other threads the property s_MemoryInitialized alone never had: they
// genuinely block on the lock until initialization is fully done.
static std::recursive_mutex s_memoryInitMutex;
static std::mutex s_standardMutex;
static std::mutex s_virtualMutex;
#endif

/**
 * Offset/Address/Size: 0x0 | 0x801D1EE4 | size: 0x40
 */
void nlFree(void* ptr)
{
#ifndef TARGET_PC
    if (((uint)ptr & 0x80000000) == 0)
    {
        VirtualAllocator.Free(ptr);
    }
    else
    {
        StandardAllocator.Free(ptr);
    }
#else
    if (ptr >= g_virtualBase && (uintptr_t)ptr < (uintptr_t)g_virtualBase+g_virtualSize)
    {
        const std::lock_guard<std::mutex> lock(s_virtualMutex);
        VirtualAllocator.Free(ptr);
    }
    else if (ptr >= g_standardBase && (uintptr_t)ptr < (uintptr_t)g_standardBase + g_standardSize)
    {
        const std::lock_guard<std::mutex> lock(s_standardMutex);
        StandardAllocator.Free(ptr);
    }
    else
    {
        free(ptr);
    }
#endif
}

/**
 * Offset/Address/Size: 0x40 | 0x801D1F24 | size: 0x64
 */
void* nlMalloc(unsigned long size, unsigned int alignment, bool atEnd)
{
#ifdef TARGET_PC
    if (!g_EngineArenaReady)
    {
        return malloc(size);
    }
    // Unlike the console path below, this can't fast-path on a plain,
    // unsynchronized read of s_MemoryInitialized: another thread could see it
    // flip to 1 (set as the very first step inside nlInitMemory's guarded
    // block) and skip straight to StandardAllocator.Allocate() while
    // InitializeStandardAndVirtualAllocators() is still running on the
    // initializing thread.
    nlInitMemory();
#else
    if (s_MemoryInitialized == 0)
    {
        nlInitMemory();
    }
#endif
#ifdef TARGET_PC
    const std::lock_guard<std::mutex> lock(s_standardMutex);
    void* result = StandardAllocator.Allocate(size, alignment, atEnd);
    return result;
#else
    return StandardAllocator.Allocate(size, alignment, atEnd);
#endif
}

/**
 * Offset/Address/Size: 0xA4 | 0x801D1F88 | size: 0x4C
 */
void* nlMalloc(unsigned long size)
{
#ifdef TARGET_PC
    if (!g_EngineArenaReady)
    {
        return malloc(size);
    }
    // See nlMalloc(size, alignment, atEnd) above.
    nlInitMemory();
#else
    if (s_MemoryInitialized == 0)
    {
        nlInitMemory();
    }
#endif
#ifdef TARGET_PC
    const std::lock_guard<std::mutex> lock(s_standardMutex);
    void* result = StandardAllocator.Allocate(size, 8, false);
    return result;
#else
    return StandardAllocator.Allocate(size, 8, false);
#endif
}

/**
 * Offset/Address/Size: 0x1BC | 0x801D20A0 | size: 0x24
 */
unsigned int nlVirtualTotalFree()
{
    return VirtualAllocator.TotalFreeMemory();
}

/**
 * Offset/Address/Size: 0x1E0 | 0x801D20C4 | size: 0x24
 */
unsigned int nlVirtualLargestBlock()
{
    return VirtualAllocator.LargestFreeBlock();
}

/**
 * Offset/Address/Size: 0x204 | 0x801D20E8 | size: 0x28
 */
void nlVirtualFree(void* ptr)
{
#ifdef TARGET_PC
    const std::lock_guard<std::mutex> lock(s_virtualMutex);
    VirtualAllocator.Free(ptr);
#else
    VirtualAllocator.Free(ptr);
#endif
}

/**
 * Offset/Address/Size: 0x22C | 0x801D2110 | size: 0x30
 */
void* nlVirtualAlloc(unsigned long size, bool bZero)
{
#ifdef TARGET_PC
    const std::lock_guard<std::mutex> lock(s_virtualMutex);
    void* result = VirtualAllocator.Allocate(size, 0x20, bZero);
    return result;
#else
    return VirtualAllocator.Allocate(size, 0x20, bZero);
#endif
}

static void InitializeStandardAndVirtualAllocators()
{
        void* arenaLo = OSGetArenaLo();
        void* arenaHi = OSGetArenaHi();
        arenaLo = OSInitAlloc(arenaLo, arenaHi, 1);
        OSSetArenaLo(arenaLo);

#ifndef TARGET_PC
        u32 alignedLo = ((u32)arenaLo + 0x1F) & ~0x1F;
        arenaLo = (void*)((u32)arenaHi & ~0x1F);
        u32 heapSize = (u32)arenaLo - alignedLo;
#else
        uintptr_t alignedLo = ((uintptr_t)arenaLo + 0x1F) & ~0x1F;
        arenaLo = (void*)((uintptr_t)arenaHi & ~0x1F);
        uintptr_t heapSize = (uintptr_t)arenaLo - alignedLo;
#endif

#ifndef TARGET_PC
        s32 heap = OSCreateHeap((void*)alignedLo, arenaLo);
#else
        OSHeapHandle heap = OSCreateHeap((void*)alignedLo, arenaLo);
#endif
        OSSetCurrentHeap(heap);
        OSSetArenaLo(arenaLo);

#ifdef TARGET_PC
        uintptr_t standardSize = heapSize - 0x40000 - g_virtualSize;
#else
        uintptr_t standardSize = heapSize - 0x40000;
#endif
        void* ptr = OSAllocFromHeap(__OSCurrHeap, standardSize);
#ifndef TARGET_PC
        u32 i;
#else
        uintptr_t i;
#endif
        for (i = 0; i < standardSize; i++)
        {
            ((s8*)ptr)[i] = -0x33;
        }

        StandardAllocator.Initialize(ptr, standardSize);
#ifdef TARGET_PC
        g_standardBase = ptr;
        g_standardSize = standardSize;
#endif
#ifndef TARGET_PC
        VirtualAllocator.Initialize((void*)0x7E000000, 0x900000);
#else
        void* virtPtr = OSAllocFromHeap(__OSCurrHeap, g_virtualSize);
        VirtualAllocator.Initialize(virtPtr, g_virtualSize);
        g_virtualBase = virtPtr;
#endif
}

/**
 * Offset/Address/Size: 0x25C | 0x801D2140 | size: 0x1B8
 */
void nlInitMemory()
{
#ifndef TARGET_PC
    if (s_MemoryInitialized == 0)
    {
        s_MemoryInitialized = 1;
        VMInit(0x100000, 0x700000, 0x900000);
        VMAlloc(0x7E000000, 0x900000);
        DVDInit();
        VIInit();
        PADInit();
        InitializeStandardAndVirtualAllocators();
        OSReport("After nlInitMemory\n");
        OSReport("Free Memory: %u\n", StandardAllocator.TotalFreeMemory());
        OSReport("Largest Free Block: %u\n", StandardAllocator.LargestFreeBlock());
    }
#else
    const std::lock_guard<std::recursive_mutex> initLock(s_memoryInitMutex);
    if (s_MemoryInitialized == 0)
    {
        s_MemoryInitialized = 1;
        InitializeStandardAndVirtualAllocators();
        VMInit(0x100000, 0x700000, 0x900000);
        VMAlloc(0x7E000000, 0x900000);
        DVDInit();
        VIInit();
        PADInit();
        OSReport("After nlInitMemory\n");
        OSReport("Free Memory: %u\n", StandardAllocator.TotalFreeMemory());
        OSReport("Largest Free Block: %u\n", StandardAllocator.LargestFreeBlock());
    }
#endif
}
#ifdef TARGET_PC
// ---------------------------------------------------------------------
// Global operator new/delete overrides — see nlMemory.h for rationale.
// ---------------------------------------------------------------------

// The C++ ABI guarantees that the plain (non-aligned) forms of operator new
// return memory aligned to __STDCPP_DEFAULT_NEW_ALIGNMENT__ (16 on x86-64).
// nlMalloc(size) defaults to 8 (the GameCube value), which is fine for the
// game's own code but breaks any host library that emits SSE aligned
// accesses (movaps/movdqa) on heap objects -- e.g. Dawn's MutexProtected.
static constexpr unsigned int kDefaultNewAlign = __STDCPP_DEFAULT_NEW_ALIGNMENT__;

void* operator new(unsigned long size)
{
    return nlMalloc(size, kDefaultNewAlign, false);
}
void* operator new[](unsigned long size)
{
    return nlMalloc(size, kDefaultNewAlign, false);
}
void operator delete(void* ptr) noexcept
{
    nlFree(ptr);
}
void operator delete[](void* ptr) noexcept
{
    nlFree(ptr);
}
void operator delete(void* ptr, unsigned long /*size*/) noexcept
{
    nlFree(ptr);
}
void operator delete[](void* ptr, unsigned long /*size*/) noexcept
{
    nlFree(ptr);
}

void* operator new(unsigned long size, const std::nothrow_t&) noexcept
{
    return nlMalloc(size, kDefaultNewAlign, false);
}
void* operator new[](unsigned long size, const std::nothrow_t&) noexcept
{
    return nlMalloc(size, kDefaultNewAlign, false);
}
void operator delete(void* ptr, const std::nothrow_t&) noexcept
{
    nlFree(ptr);
}
void operator delete[](void* ptr, const std::nothrow_t&) noexcept
{
    nlFree(ptr);
}

void* operator new(unsigned long size, std::align_val_t align)
{
    return nlMalloc(size, static_cast<unsigned int>(align), false);
}
void* operator new[](unsigned long size, std::align_val_t align)
{
    return nlMalloc(size, static_cast<unsigned int>(align), false);
}
void operator delete(void* ptr, std::align_val_t /*align*/) noexcept
{
    nlFree(ptr);
}
void operator delete[](void* ptr, std::align_val_t /*align*/) noexcept
{
    nlFree(ptr);
}

void operator delete(void* ptr, unsigned long /*size*/, std::align_val_t /*align*/) noexcept
{
    nlFree(ptr);
}
void operator delete[](void* ptr, unsigned long /*size*/, std::align_val_t /*align*/) noexcept
{
    nlFree(ptr);
}

void* operator new(unsigned long size, std::align_val_t align, const std::nothrow_t&) noexcept
{
    return nlMalloc(size, static_cast<unsigned int>(align), false);
}
void* operator new[](unsigned long size, std::align_val_t align, const std::nothrow_t&) noexcept
{
    return nlMalloc(size, static_cast<unsigned int>(align), false);
}
void operator delete(void* ptr, std::align_val_t /*align*/, const std::nothrow_t&) noexcept
{
    nlFree(ptr);
}
void operator delete[](void* ptr, std::align_val_t /*align*/, const std::nothrow_t&) noexcept
{
    nlFree(ptr);
}
#endif
