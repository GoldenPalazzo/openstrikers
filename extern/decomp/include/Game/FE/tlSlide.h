#ifndef _TLSLIDE_H_
#define _TLSLIDE_H_

#include "types.h"

#include "Game/FE/tlInstance.h"
#include "Game/FE/feAnimation.h"

enum eTimeLinePlayMode
{
    TLPM_STOP_AT_END = 0,
    TLPM_LOOPING = 1,
};

class TLSlide
{
public:
    f32 GetCurrentTime() const
    {
        return m_time;
    }
    void Update(float time);
    void UpdateAsset(TLInstance* instance, float time);

    /* 0x00 */ port::SelfRelPtr32<TLSlide> m_next;
    /* 0x04 */ char pad0[0x4];
    /* 0x08 */ port::SelfRelPtr32<TLInstance> m_instances;
    /* 0x0C */ port::SelfRelPtr32<FEAnimation> m_animations;
    /* 0x10 */ port::be<f32> m_start;
    /* 0x14 */ port::be<f32> m_duration;
    /* 0x18 */ port::be<f32> m_time;
    /* 0x1C */ port::be<eTimeLinePlayMode> m_uPlayMode;
    /* 0x20 */ char m_szName[32];
    /* 0x40 */ port::be<u32> m_hash;
};

#endif // _TLSLIDE_H_
