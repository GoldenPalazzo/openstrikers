#include "NL/nlTextEscape.h"

#include "NL/nlAlgorithm.h"
#ifdef TARGET_PC
#include "port/endian.hpp"
#endif

#ifndef TARGET_PC
extern "C" unsigned long wcstoul(const unsigned short* str, unsigned short** end, int base);
#else
// override glibc's wcstoul that takes 32-bit wchar_t but game strings are u16
static unsigned long wcstoul(const unsigned short* str, unsigned short** end, int base)
{
    unsigned long value = 0;
    for (; *str != 0; str++)
    {
        unsigned short c = *str;
        int digit;
        if (c >= '0' && c <= '9')
            digit = c - '0';
        else if (c >= 'a' && c <= 'z')
            digit = c - 'a' + 10;
        else if (c >= 'A' && c <= 'Z')
            digit = c - 'A' + 10;
        else
            break;
        if (digit >= base)
            break;
        value = value * base + digit;
    }
    if (end != 0)
        *end = (unsigned short*)str;
    return value;
}
#endif

const unsigned long nlEscapeSequence::ESCAPE_DEFN[ESC_COUNT] = {
    0x00000000,
    0x7B000000,
    0x6E627300,
    0x636C7200,
    0x70000000,
};

nlEscapeSequence::ESCAPE_LOOKUP nlEscapeSequence::s_EscapeLookup[ESC_COUNT];

const unsigned short nlEscapeSequence::ESCAPE_BEGIN = 0x007B;

class EscapeSorter
{
public:
    EscapeSorter()
    {
        for (int i = 0; i < ESC_COUNT; i++)
        {
            nlEscapeSequence::s_EscapeLookup[i].hash = nlEscapeSequence::ESCAPE_DEFN[i];
            nlEscapeSequence::s_EscapeLookup[i].type = (ESCAPE_TYPE)i;
        }
        nlQSort<nlEscapeSequence::ESCAPE_LOOKUP>(nlEscapeSequence::s_EscapeLookup, ESC_COUNT, &nlDefaultQSortComparer<nlEscapeSequence::ESCAPE_LOOKUP>);
    }
};

static EscapeSorter s_EscapeSorter;

/**
 * Offset/Address/Size: 0xB0 | 0x802125CC | size: 0x174
 */
nlEscapeSequence::nlEscapeSequence(const unsigned short* str)
{
#ifndef TARGET_PC
    char Seq[4] = { 0, 0, 0, 0 };
#else
    u32 Seq = 0;
#endif
    const unsigned short* ExtendedStart = 0;
    const unsigned short* p = str;
#ifndef TARGET_PC
    char* pSeq = Seq;
#else
    char* pSeq = (char*)&Seq;
#endif
    unsigned long Char = 0;
    unsigned long key;
    ESCAPE_LOOKUP* pEscape;
    ESCAPE_TYPE type;

    while (true)
    {
        unsigned long ch = p[1];

        if (ch == '}')
        {
            break;
        }

        if (ch == ':')
        {
            const unsigned short* pExtended = str;
            pExtended += Char;
            ExtendedStart = pExtended + 2;
            break;
        }

        if (Char < 4)
        {
            *pSeq = (char)ch;
        }

        p++;
        pSeq++;
        Char++;
    }

    if (ExtendedStart != 0)
    {
        nlEscapeSequence* pSelf = this;

        for (Char = 0; Char < 15; Char++)
        {
            unsigned long ch = ExtendedStart[Char];
            if (ch == '}')
            {
                break;
            }

            pSelf->m_Extended[Char] = (unsigned short)ch;
        }
    }

    m_Extended[Char] = 0;
    m_pEnd = (ExtendedStart ? ExtendedStart : str + 1) + Char + 1;

#ifndef TARGET_PC
    key = *(unsigned long*)Seq;
#else
    key = bswap(Seq);
#endif
    pEscape = nlBSearch(key, s_EscapeLookup, ESC_COUNT);
    if (pEscape != 0)
    {
        type = pEscape->type;
    }
    else
    {
        type = ESC_UNKNOWN;
    }
    m_Type = type;
}

/**
 * Offset/Address/Size: 0x0 | 0x8021251C | size: 0xB0
 */
nlColour nlEscapeSequence::GetExtendedColour()
{
    unsigned short str[3] = { 0, 0, 0 };
    nlColour colour;

    if ((int)m_Extended[0] == 0x70)
    {
        colour.c[3] = 0;
        return colour;
    }

    int channel = 0;
    for (channel = 0; channel < 3; channel++)
    {
        str[0] = m_Extended[channel * 2];
        str[1] = m_Extended[channel * 2 + 1];
        colour.c[channel] = (u8)wcstoul(str, 0, 16);
    }
    colour.c[3] = 0xFF;
    return colour;
}
