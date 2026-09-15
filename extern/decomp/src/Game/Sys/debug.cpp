
#include "Game/Sys/debug.h"
#include "Game/Sys/simpleparser.h"

#include "extras.h"
#include "NL/nlFileGC.h"
// #include "NL/nlPrint.h"

extern int nlPrintf(const char*, ...);

namespace tDebugPrintManager
{

const char* szChannelNames[DC_NUM_CHANNELS] = {
    "STARTUP",
    "GL",
    "GLPLAT",
    "RENDER",
    "AI",
    "CAMERA",
    "EVENT",
    "FE",
    "PHYSICS",
    "MEMORY",
    "SOUND",
    "TASKMAN",
    "LOADER",
    "MISC",
    "REPLAY",
    "NIS",
    "NET",
    "MULTISTREAM",
    "WORLD",
    "CONFIGSYS",
};

bool abChannels[DC_NUM_CHANNELS] = { true, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false };

/**
 * Offset/Address/Size: 0x0 | 0x801D6770 | size: 0x54
 */
int Print(eDEBUG_CHANNEL channel, const char* format, ...)
{
    return 0;
}

/**
 * Offset/Address/Size: 0x54 | 0x801D67C4 | size: 0xE8
 */
void Initialize()
{
    // Zero out all channels
    for (int i = 0; i < DC_NUM_CHANNELS; ++i)
        abChannels[i] = 0;

    // Parse file; if it fails, enable all
    if (ParseDebugChannelFile("PrintCfg.txt") == 0)
    {
        for (int i = 0; i < DC_NUM_CHANNELS; ++i)
        {
            abChannels[i] = 1;
        }
    }
}

/**
 * Offset/Address/Size: 0x13C | 0x801D68AC | size: 0xF8
 */
bool ParseDebugChannelFile(const char* path)
{
    SimpleParser parser;
    u32 uFileSize;
    char* token;

    char* pData = (char*)nlLoadEntireFile(path, &uFileSize, 0x20u, AllocateStart);
    if (!pData)
    {
        nlPrintf("Failed to load file %s.  All print channels will be enabled.\n", path);
        return false;
    }

    if (parser.StartParsing(pData, uFileSize, true))
    {
        for (;;)
        {
            token = parser.NextToken(true);
            if (!token)
                break;

            // skip comment lines starting with '#'
            if (token[0] == '#')
                continue;

            // scan list of known channel names and mark enabled
            for (int chan = 0; chan < DC_NUM_CHANNELS; ++chan)
            {
                if (strcmpi(szChannelNames[chan], token) == 0)
                {
                    abChannels[chan] = 1;
                }
            }
        }
    }

    nlFree(pData);
    return true;
}

} // namespace tDebugPrintManager
