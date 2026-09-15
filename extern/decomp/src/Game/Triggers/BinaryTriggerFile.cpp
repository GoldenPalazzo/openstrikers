#include "Game/Triggers/BinaryTriggerFile.h"

#include "NL/nlFile.h"

/**
 * Offset/Address/Size: 0x0 | 0x802142DC | size: 0x78
 */
BinaryTriggerFile::BinaryTriggerFile(const char* FileName)
{
    m_pFileData = NULL;
    m_pCurrentAnim = 0;
    m_CurrentTrigger = 0;
    m_pFileData = (FILE_HEADER*)nlLoadEntireFile(FileName, &m_FileSize, 0x20, AllocateEnd);
    m_pFirstAnim = (ANIM_RECORD*)((u8*)m_pFileData + sizeof(FILE_HEADER));
    m_pFirstTrigger = (TRIGGER_RECORD*)((u8*)m_pFirstAnim + (m_pFileData->AnimCount * sizeof(ANIM_RECORD)));
}
