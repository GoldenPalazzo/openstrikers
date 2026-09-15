#include "Game/InterpreterCore.h"

#include "NL/nlDebug.h"
#include "NL/nlMemory.h"


/**
 * Offset/Address/Size: 0x68C | 0x802137D4 | size: 0x4C
 */
InterpreterCore::InterpreterCore(unsigned int size)
{
    m_StackSegment = (u32*)nlMalloc(size * 4);
    m_Header = NULL;
}

/**
 * Offset/Address/Size: 0x62C | 0x80213774 | size: 0x60
 */
InterpreterCore::~InterpreterCore()
{
    nlFree(m_StackSegment);
}

/**
 * Offset/Address/Size: 0x5A4 | 0x802136EC | size: 0x88
 */
void InterpreterCore::LoadByteCode(void* data)
{
    // golden TODO: potential memory leak, check later if the original data
    // gets cleaned
    ByteCodeHeaderOnDisk* diskHeader = (ByteCodeHeaderOnDisk*)data;
    m_Header = (ByteCodeHeader*)nlMalloc(sizeof(ByteCodeHeader), 8 ,false);
    m_Header->signature = diskHeader->signature;
    m_Header->numFunctions = diskHeader->numFunctions;
    m_Header->dataSegmentSize = diskHeader->dataSegmentSize;
    m_Header->codeSegmentSize = diskHeader->codeSegmentSize; 
    m_Header->stringSegmentSize = diskHeader->stringSegmentSize;
    // golden TODO: original was ByteCodeHeader+1, check if offset is correct
    m_Header->m_FunctionTable = (FunctionEntryPoint*)((u8*)data + 0x24);
    m_Header->m_DataSegment = (u32*)(m_Header->m_FunctionTable + m_Header->numFunctions);
    m_Header->m_CodeSegment = (u16*)((u8*)m_Header->m_DataSegment + m_Header->dataSegmentSize);
    m_Header->m_StringSegment = (u8*)m_Header->m_CodeSegment + m_Header->codeSegmentSize;
    fprintf(stderr, "[DEBUG] numFunctions=%u m_FunctionTable=%p first_hash=0x%x\n",
        m_Header->numFunctions, (void*)m_Header->m_FunctionTable,
        m_Header->numFunctions > 0 ? static_cast<u32>(m_Header->m_FunctionTable[0].hash) : 0);

    m_SP = m_StackSegment;
    m_SavedSP = m_SP;
    m_IP = m_Header->m_CodeSegment;
    m_BP = m_SP;

    m_RunState = 0;
}

/**
 * Offset/Address/Size: 0x4C4 | 0x8021360C | size: 0xE0
 */
void InterpreterCore::CallFunction(unsigned long hash)
{
    FunctionEntryPoint* fnc_ptr = (FunctionEntryPoint*)nlBSearch<FunctionEntryPoint, u32>(hash, m_Header->m_FunctionTable, m_Header->numFunctions);
    m_IP = (u16*)((u8*)m_Header->m_CodeSegment + fnc_ptr->offset);

    m_SP = m_StackSegment;
    m_SavedSP = m_SP;
    m_BP = m_SP;
    m_RunState = 0;

    if (m_RunState != 2)
    {
        if (m_RunState == 0)
        {
            *m_SP = 0;
            m_SP++;
            m_RunState = 1;
        }
        m_Stop = 0;

        while (!m_Stop)
        {
            Step();
        }
    }
}

/**
 * Offset/Address/Size: 0x400 | 0x80213548 | size: 0xC4
 */
void InterpreterCore::CallFunctionAt(unsigned long offset)
{
    m_IP = (u16*)((u8*)m_Header->m_CodeSegment + offset);
    m_SP = m_StackSegment;
    m_SavedSP = m_SP;
    m_BP = m_SP;
    m_RunState = 0;

    if (m_RunState != 2)
    {
        if (m_RunState == 0)
        {
            *m_SP = 0;
            m_SP++;
            m_RunState = 1;
        }
        m_Stop = 0;

        while (!m_Stop)
        {
            Step();
        }
    }
}

/**
 * Offset/Address/Size: 0x3C0 | 0x80213508 | size: 0x40
 */
bool InterpreterCore::FunctionExists(unsigned long hash)
{
    FunctionEntryPoint* pEntry;
    ByteCodeHeader* pHeader;

    pHeader = m_Header;
    pEntry = nlBSearch<FunctionEntryPoint, u32>(hash, pHeader->m_FunctionTable, pHeader->numFunctions);
    return pEntry != NULL;
}

/**
 * Offset/Address/Size: 0x330 | 0x80213478 | size: 0x90
 */
void InterpreterCore::Run()
{
    if (m_RunState != 2)
    {
        if (m_RunState == 0)
        {
            *m_SP = 0;
            m_SP++;
            m_RunState = 1;
        }
        m_Stop = 0;

        while (!m_Stop)
        {
            Step();
        }
    }
}

/**
 * Offset/Address/Size: 0x308 | 0x80213450 | size: 0x28
 */
void InterpreterCore::StopWithUndo()
{
    m_IP -= 1;
    m_SP = m_SavedSP;
    m_Stop = 1;
}

/**
 * Offset/Address/Size: 0x18 | 0x80213160 | size: 0x2F0
 */
void InterpreterCore::Step()
{
    u16 instr;
    u16 op_high;
    u16 op_low;
    u32* volatile saved_bp;
    u16* volatile saved_ip;

    instr = *m_IP;
    op_high = instr & 0xC000;
    op_low = instr & 0x3FFF;

    switch (op_high)
    {
    case 0x0000:
        *m_SP = m_Header->m_DataSegment[op_low];
        m_SP++;
        break;

    case 0x4000:
        *m_SP = (u32)(m_Header->m_StringSegment + op_low);
        m_SP++;
        break;

    case 0x8000:
        m_SavedSP = m_SP;
        DoFunctionCall(op_low);
        break;

    case 0xC000:
        switch ((op_low >> 8) & 0xFF)
        {
        case 0x0:
            saved_bp = m_BP;
            *m_SP = (u32)m_BP;
            m_SP++;
            m_BP = m_SP;
            m_SP += (op_low & 0xFF);
            break;

        case 0x1:
            m_SP -= (op_low & 0xFF);
            m_SP--;
            m_BP = (u32*)(*m_SP);
            break;

        case 0x2:
            m_SP--;
            m_IP = (u16*)(*m_SP);
            m_SP -= (op_low & 0xFF);
            if (!m_IP)
            {
                m_Stop = 1;
                m_RunState = 2;
                return;
            }
            break;

        case 0x3:
        {
            s8 offset = (s8)(op_low & 0xFF);
            *m_SP = m_BP[offset];
            m_SP++;
            break;
        }

        case 0x4:
        {
            s8 offset = (s8)(op_low & 0xFF);
            m_SP--;
            m_BP[offset] = *m_SP;
            break;
        }

        case 0x5:
            m_SP--;
            m_Return = *m_SP;
            break;

        case 0x6:
            *m_SP = m_Return;
            m_SP++;
            break;

        case 0x7:
        {
            s8 offset = (s8)(op_low & 0xFF);
            m_BP[offset] = m_Return;
            break;
        }

        case 0x8:
        {
            s8 offset = (s8)(op_low & 0xFF);
            m_Return = m_BP[offset];
            break;
        }

        case 0x9:
            *m_SP = (op_low & 0xFF);
            m_SP++;
            break;

        case 0xA:
        {
            u8 index;
            saved_ip = m_IP;
            *m_SP = (u32)m_IP;
            m_SP++;
            index = (u8)(op_low & 0xFF);
            m_IP = (u16*)((u8*)m_Header->m_CodeSegment + (m_Header->m_FunctionTable[index].offset & ~1));
            return;
        }

        default:
            nlBreak();
            break;
        }
        break;
    }

    m_IP += 1;
}
/**
 * Offset/Address/Size: 0x0 | 0x80213148 | size: 0x18
 */
bool InterpreterCore::IsFinished() const
{
    return m_RunState == 2;
}
