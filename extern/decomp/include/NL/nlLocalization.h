#ifndef _NLLOCALIZATION_H_
#define _NLLOCALIZATION_H_

#ifdef TARGET_PC
#include "port/endian.hpp"
#endif

struct LOCHeader
{
    char Thumbprint[4];
#ifndef TARGET_PC
    unsigned long Version;
    unsigned long Language;
    unsigned long StringCount;
    unsigned long Flags;
#else
    port::be<u32> Version;
    port::be<u32> Language;
    port::be<u32> StringCount;
    port::be<u32> Flags;
#endif
};

class nlLocalization
{
public:
    struct StringLookup
    {
#ifndef TARGET_PC
        unsigned long hash;
        unsigned long StringOffset;

        operator unsigned long() const { return hash; }
#else
        port::be<u32> hash;
        port::be<u32> StringOffset;

        operator u32() const { return hash; }
#endif
    };

    enum nlLanguage
    {
        LangEnglish = 0,
        LangFrench = 1,
        LangGerman = 2,
        LangSpanish = 3,
        LangItalian = 4,
        LangJapanese = 5,
        LangUKEnglish = 6,
        LangLongestStrings = 7,
        LangBob = 8,
        LangEnd = 9,
    };

    unsigned char Load(nlLanguage Language, bool ingameloc);
    void Destroy();
    static void Initialize();

    LOCHeader* m_pFile;
    StringLookup* m_LookupTable;
    unsigned short* m_FirstString;
    nlLanguage m_CurrentLanguage;

#ifdef TARGET_PC
    static const char* LanguageName[];
#else
    static char* LanguageName[];
#endif
    static const unsigned long LanguageId[];
    static const char Thumbprint[4];
};

extern nlLocalization* g_pLocalization;
extern const unsigned short LocalizationTableNotFound[];
extern const unsigned short MissingLocString[];
#ifdef TARGET_PC
const unsigned short* staticLocArena(const unsigned short* pString);
#endif

#endif // _NLLOCALIZATION_H_
