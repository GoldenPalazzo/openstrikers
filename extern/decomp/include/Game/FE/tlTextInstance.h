#ifndef _TLTEXTINSTANCE_H_
#define _TLTEXTINSTANCE_H_

#include "types.h"
#include "NL/nlColour.h"
#include "NL/gl/gl.h"
#include "NL/nlFont.h"
#include "NL/nlMath.h"
#include "NL/nlTextBox.h"

#include "Game/FE/tlInstance.h"

#ifdef TARGET_PC
#include "port/endian.hpp"
#include "port/feDisk.hpp"
#endif

struct FETextLibObjectAttributes
{
    /* 0x0 */ nlColour EffectColour;
#ifndef TARGET_PC
    /* 0x4 */ nlVector2 BoxSize;
#else
    /* 0x4 */ feVector2 BoxSize;
#endif
}; // total size: 0xC

class TLTextInstance : public TLInstance
{
public:
    void SetScissorBox(u16 left, u16 top, u16 width, u16 height);
    void SetString(const unsigned short* utf16);
    void DisableScissorBox();
    void SetStringId(const char* id);
    const unsigned short* GetString() const;
    void SetMatrix(nlMatrix4* pMatrix)
#ifndef TARGET_PC
    {
        m_DrawInfo.pMatrix = pMatrix;
    }
#else
    ;
#endif
    void Render(eGLView view, const nlColour& colour) const;

#ifndef TARGET_PC
    /* 0x80 */ unsigned long m_LocStrId;
#else
    /* 0x80 */ port::be<u32> m_LocStrId;
#endif
    /* 0x84 */ FETextLibObjectAttributes m_OverloadedAttributes;
#ifndef TARGET_PC
    /* 0x90 */ unsigned long m_OverloadFlags;
#else
    /* 0x90 */ port::be<u32> m_OverloadFlags;
#endif
    /* 0x94 */ mutable nlTextBox::StringDrawInfo m_DrawInfo;
#ifndef TARGET_PC
    /* 0xEC */ FontCharString* m_pFontString;
    /* 0xF0 */ unsigned long m_DrawOptions;
    /* 0xF4 */ const unsigned short* m_wcUserString;
#else
    /* 0xEC */ mutable port::UnrelocatedRelPtr32<FontCharString> m_pFontString;
    /* 0xF0 */ port::be<u32> m_DrawOptions;
    /* 0xF4 */ mutable port::UnrelocatedRelPtr32<const unsigned short> m_wcUserString;
#endif
    /* 0xF8 */ bool m_UseScissorRect;
#ifndef TARGET_PC
    /* 0xFA */ nlFont::ScissorBox m_ScissorRect;

#else
    /* 0xFA */ FEScissorBox m_ScissorRect;
#endif
}; // total size: 0x104

#endif // _TLTEXTINSTANCE_H_
