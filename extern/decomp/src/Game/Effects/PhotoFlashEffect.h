#ifndef _PHOTOFLASHEFFECT_H_
#define _PHOTOFLASHEFFECT_H_

#include "types.h"

class PhotoFlash
{
public:
    void Flash();
    void Render(float dt);

    static s32 sNumFramesSinceFlash;
};

#endif // _PHOTOFLASHEFFECT_H_
