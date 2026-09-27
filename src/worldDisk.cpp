#include "port/worldDisk.hpp"
#include "Game/Physics/CharacterPhysicsElement.h"
#include <cstring>

namespace port::disk {

void convert(::CharacterPhysicsElement& out, const CharacterPhysicsElement& in)
{
    for (int i=0; i<16; i++)
        out.matLocalToParent.e[i] = in.matLocalToParent[i];
    memcpy(out.szName, in.szName, 32);
    out.uHashID = in.uHashID;
    memcpy(out.szParentName, in.szParentName, 32);
    out.uParentHashID= in.uParentHashID;
    out.uPrimitiveType= in.uPrimitiveType;
    out.fWidth       = in.fWidth;
    out.fLength      = in.fLength;
    out.fHeight      = in.fHeight;
    out.fRadius      = in.fRadius;
    out.uReserved    = in.uReserved;

}

}
