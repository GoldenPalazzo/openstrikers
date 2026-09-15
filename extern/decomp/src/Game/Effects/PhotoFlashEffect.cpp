#include "PhotoFlashEffect.h"

#include "NL/nlColour.h"
#include "NL/gl/glState.h"
#include "NL/gl/glDraw2.h"

static s32 sNumFlashFadeFrames = 8;

s32 PhotoFlash::sNumFramesSinceFlash = 999;

/**
 * Offset/Address/Size: 0xC4 | 0x8016B024 | size: 0xC
 */
void PhotoFlash::Flash()
{
    sNumFramesSinceFlash = 0;
}

/**
 * Offset/Address/Size: 0x0 | 0x8016AF60 | size: 0xC4
 */
void PhotoFlash::Render(float dt)
{
    glPoly2 poly;
    u8 value;
    if (sNumFramesSinceFlash < sNumFlashFadeFrames)
    {
        glSetDefaultState(false);
        glSetRasterState(GLS_AlphaBlend, 2);
        glSetCurrentRasterState(glHandleizeRasterState());

        value = 255 - ((0xFF / sNumFlashFadeFrames) * sNumFramesSinceFlash);

        nlColour c = { 0, 0, 0, 0 };
        c.c[0] = value;
        c.c[1] = value;
        c.c[2] = value;
        c.c[3] = 255;

        poly.SetColour(c);
        poly.SetupRectangle(0.0f, 0.0f, 640.0f, 480.0f, 0.0f);
        glAttachPoly2(GLV_FrontEnd, 1, &poly, 0, 0);
    }

    ++sNumFramesSinceFlash;
}
