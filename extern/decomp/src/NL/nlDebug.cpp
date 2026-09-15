#include "NL/nlDebug.h"

#include "types.h"

/**
 * Offset/Address/Size: 0x0 | 0x801CE948 | size: 0xC
 */
void nlBreak()
{
    *(u32*)1 = 0;
}
