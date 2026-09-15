#ifndef _TLCOMPONENT_H_
#define _TLCOMPONENT_H_

#include "NL/nlMath.h"
#include "types.h"

#include "Game/FE/feLibObject.h"

#include "port/endian.h"

class TLSlide;

class TLComponent : public FELibObject
{
public:
    TLSlide* GetActiveSlide()
    {
        return m_pActiveSlide;
    }
    void SetActiveSlide(unsigned long hash);
    void SetActiveSlide(const char* name);

    /* 0x68 */ port::SelfRelPtr32<TLSlide> pChildren;
    /* 0x6C */ port::SelfRelPtr32<TLSlide> m_pActiveSlide;
    /* 0x70 */ nlVector2 m_BoxSize; // something is fishy here -> feHelpFuncs/MakeTextBoxReallyWide needs a nlVector2 here.
    /* 0x70 */ char m_szName[32];
    /* 0x90 */ port::be<u32> m_hashID;
}; // total size: 0x94

#endif // _TLCOMPONENT_H_
