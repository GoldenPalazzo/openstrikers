#pragma once
#include "NL/nlMath.h"
#include "endian.hpp"

struct CharacterPhysicsElement;
namespace port::disk {
struct CharacterPhysicsElement
{
    /* 0x00 */ port::be<f32> matLocalToParent[16];
    /* 0x40 */ s8 szName[32];
    /* 0x60 */ port::be<u32> uHashID;
    /* 0x64 */ s8 szParentName[32];
    /* 0x84 */ port::be<u32> uParentHashID;
    /* 0x88 */ port::be<u32> uPrimitiveType;
    /* 0x8C */ port::be<f32> fWidth;
    /* 0x90 */ port::be<f32> fLength;
    /* 0x94 */ port::be<f32> fHeight;
    /* 0x98 */ port::be<f32> fRadius;
    /* 0x9C */ port::be<u32> uReserved;
}; // total size: 0xA0

static_assert(sizeof(CharacterPhysicsElement) == 0xA0);

void convert(::CharacterPhysicsElement& out, const CharacterPhysicsElement& in);
}
