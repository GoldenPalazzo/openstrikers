/*
 * Special thanks to JackPriceBurns on GitHub, the porter of Star Fox
 * Adventures for helping me with this. The repo was easy enough to understand
 * the bare minimum needed to integrate aurora.
 * This code is pretty much copied from "vi_shim.cpp", so all credits go to
 * the original author, not me.
 */

#include <cstdlib>

#include <aurora/aurora.h>
#include <aurora/dvd.h>
#include <aurora/event.h>
#include <dolphin/vi.h>

static VIRetraceCallback s_preretracecb;
static VIRetraceCallback s_postretracecb;
static void* s_nextfb;
static bool s_frameopen = false;
static u32 s_retracecnt;

static void pump_events()
{
    const AuroraEvent* event = aurora_update();
    for (; event != NULL && event->type != AURORA_NONE; event++)
    {
        if (event->type == AURORA_EXIT)
        {
            aurora_dvd_close();
            aurora_shutdown();
            exit(0);
        }
    }
}

void framepump_init() {
    pump_events();
    s_frameopen = aurora_begin_frame();
}

void VISetBlack(int) {}
void VIWaitForRetrace()
{
    if (s_frameopen)
    {
        aurora_end_frame();
        s_frameopen = false;
    }

    pump_events();
    while (!aurora_begin_frame())
        pump_events();

    s_frameopen = true;

    s_retracecnt++;
    if (s_preretracecb)
        s_preretracecb(s_retracecnt);
    if (s_postretracecb)
        s_postretracecb(s_retracecnt);
}

u32 VIGetRetraceCount() { return s_retracecnt; }
void VISetNextFrameBuffer(void* fb)
{
    s_nextfb = fb;
}
void* VIGetNextFrameBuffer()
{
    return s_nextfb;
}
VIRetraceCallback VISetPreRetraceCallback(VIRetraceCallback cb)
{
    VIRetraceCallback prev = s_preretracecb;
    s_preretracecb = cb;
    return prev;
}
VIRetraceCallback VISetPostRetraceCallback(VIRetraceCallback cb)
{
    VIRetraceCallback prev = s_postretracecb;
    s_postretracecb = cb;
    return prev;
}
u32 VIGetDTVStatus() { return 1; }
