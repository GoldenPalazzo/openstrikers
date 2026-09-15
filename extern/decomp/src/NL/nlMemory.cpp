#include "NL/nlMemory.h"
#include "NL/MemAlloc.h"

#include <types.h>

#include "dolphin/os.h"
#include "dolphin/pad.h"
#include "dolphin/dvd.h"
#include "dolphin/vm/VM.h"
#include "dolphin/vi/vifuncs.h"

static u8 s_MemoryInitialized = 0;
// extern "C" bool g_EngineArenaReady;

MemoryAllocator StandardAllocator;
MemoryAllocator VirtualAllocator;

/**
 * Offset/Address/Size: 0x0 | 0x801D1EE4 | size: 0x40
 */
void nlFree(void* ptr)
{
    free(ptr);
}

/**
 * Offset/Address/Size: 0x40 | 0x801D1F24 | size: 0x64
 */
void* nlMalloc(unsigned long size, unsigned int alignment, bool atEnd)
{
    // if (!g_EngineArenaReady)
    // {
    //     return malloc(size);
    // }
    if (s_MemoryInitialized == 0)
    {
        nlInitMemory();
    }
    return StandardAllocator.Allocate(size, alignment, atEnd);
}

/**
 * Offset/Address/Size: 0xA4 | 0x801D1F88 | size: 0x4C
 */
void* nlMalloc(unsigned long size)
{
    // if (!g_EngineArenaReady)
    // {
    //     return malloc(size);
    // }
    if (s_MemoryInitialized == 0)
    {
        nlInitMemory();
    }
    return StandardAllocator.Allocate(size, 8, false);
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
    VirtualAllocator.Free(ptr);
}

/**
 * Offset/Address/Size: 0x22C | 0x801D2110 | size: 0x30
 */
void* nlVirtualAlloc(unsigned long size, bool bZero)
{
    return VirtualAllocator.Allocate(size, 0x20, bZero);
}

/**
 * Offset/Address/Size: 0x25C | 0x801D2140 | size: 0x1B8
 */
void nlInitMemory()
{
    if (s_MemoryInitialized == 0)
    {
        s_MemoryInitialized = 1;
        VMInit(0x100000, 0x700000, 0x900000);
        VMAlloc(0x7E000000, 0x900000);
        DVDInit();
        VIInit();
        PADInit();
        OSReport("After nlInitMemory\n");
        OSReport("Free Memory: %u\n", StandardAllocator.TotalFreeMemory());
        OSReport("Largest Free Block: %u\n", StandardAllocator.LargestFreeBlock());
    }
}

// ---------------------------------------------------------------------
// Global operator new/delete overrides — see nlMemory.h for rationale.
// ---------------------------------------------------------------------

void* operator new(unsigned long size)
{
    return nlMalloc(size);
}
void* operator new[](unsigned long size)
{
    return nlMalloc(size);
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
    return nlMalloc(size);
}
void* operator new[](unsigned long size, const std::nothrow_t&) noexcept
{
    return nlMalloc(size);
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
