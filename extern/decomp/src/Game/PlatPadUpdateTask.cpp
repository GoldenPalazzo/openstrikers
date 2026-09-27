#include "Game/PlatPadUpdateTask.h"

#include "Game/RumbleActions.h"
#ifdef TARGET_PC
#include "NL/platpad.h"
#endif

/**
 * Offset/Address/Size: 0x0 | 0x80170B80 | size: 0x20
 */
void PlatPadUpdateTask::Run(float dt)
{
#ifdef TARGET_PC
    // golden TODO: I'm fairly sure this is a bad idea, I'm not skilled enough
    // to know where this should go. But at least it works. It seems the most
    // logical place to put a routine like this
    VBlankPadUpdate();
#endif
    UpdateRumbleActions(dt);
}
