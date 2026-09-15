#ifndef _NLMEMORY_H_
#define _NLMEMORY_H_

#include "dolphin/os.h"
#include <stddef.h>
#include <new>

inline unsigned long KB(unsigned long size)
{
    return size << 10;
}

inline unsigned long MB(unsigned long size)
{
    return KB(KB(size));
}

void nlFree(void* ptr);
void* nlMalloc(unsigned long size, unsigned int alignment, bool atEnd);
void* nlMalloc(unsigned long size);

// ---------------------------------------------------------------------
// Global operator new/delete overrides.
//
// Every allocation in the process (decomp code, Aurora, and third-party
// libraries like Dawn/webgpu) goes through these, so they all end up
// funneled through nlMalloc/nlFree (StandardAllocator). This avoids
// malloc/new-delete[] mismatches under ASan, and keeps the engine's
// single allocator as the one source of truth.
//
// This is the FULL set of replaceable allocation functions per the
// C++ standard. Implementing only a subset is not safe: any library
// (e.g. Dawn) using a form you didn't override falls back to the
// system allocator, and later a `delete` on that pointer routes
// through your override -> alloc/dealloc mismatch.
// ---------------------------------------------------------------------

// Base
void* operator new(unsigned long size);
void* operator new[](unsigned long size);
void operator delete(void* ptr) noexcept;
void operator delete[](void* ptr) noexcept;

// Sized delete (C++14+)
void operator delete(void* ptr, unsigned long size) noexcept;
void operator delete[](void* ptr, unsigned long size) noexcept;

// Nothrow
void* operator new(unsigned long size, const std::nothrow_t&) noexcept;
void* operator new[](unsigned long size, const std::nothrow_t&) noexcept;
void operator delete(void* ptr, const std::nothrow_t&) noexcept;
void operator delete[](void* ptr, const std::nothrow_t&) noexcept;

// Aligned (C++17+)
void* operator new(unsigned long size, std::align_val_t align);
void* operator new[](unsigned long size, std::align_val_t align);
void operator delete(void* ptr, std::align_val_t align) noexcept;
void operator delete[](void* ptr, std::align_val_t align) noexcept;

// Aligned + sized
void operator delete(void* ptr, unsigned long size, std::align_val_t align) noexcept;
void operator delete[](void* ptr, unsigned long size, std::align_val_t align) noexcept;

// Aligned + nothrow
void* operator new(unsigned long size, std::align_val_t align, const std::nothrow_t&) noexcept;
void* operator new[](unsigned long size, std::align_val_t align, const std::nothrow_t&) noexcept;
void operator delete(void* ptr, std::align_val_t align, const std::nothrow_t&) noexcept;
void operator delete[](void* ptr, std::align_val_t align, const std::nothrow_t&) noexcept;

// ---------------------------------------------------------------------
// Engine-specific placement new: explicit alignment + "atEnd" arena
// placement, used throughout the decomp for hardware-aligned buffers
// (DMA/audio/texture data) and arena allocation. Not standard overloads,
// just custom placement-new tags routed straight to nlMalloc.
// ---------------------------------------------------------------------
inline void* operator new(unsigned long size, unsigned int alignment, bool atEnd)
{
    return nlMalloc(size, alignment, atEnd);
}
inline void* operator new[](unsigned long size, unsigned int alignment, bool atEnd)
{
    return nlMalloc(size, alignment, atEnd);
}
inline void* operator new[](unsigned long size, unsigned int alignment, bool atEnd, const char*)
{
    return nlMalloc(size, alignment, atEnd);
}

unsigned int nlVirtualTotalFree();
unsigned int nlVirtualLargestBlock();
void nlVirtualFree(void* ptr);
void* nlVirtualAlloc(unsigned long size, bool bZero);
void nlInitMemory();

#ifdef __cplusplus
extern "C"
{
#endif

#ifdef __cplusplus
}
#endif

#endif // _NLMEMORY_H_
