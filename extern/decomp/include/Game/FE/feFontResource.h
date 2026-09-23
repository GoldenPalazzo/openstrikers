#ifndef _FEFONTRESOURCE_H_
#define _FEFONTRESOURCE_H_

#include "NL/nlFont.h"
#include "Game/FE/feResourceManager.h"

#ifdef TARGET_PC
#include "port/endian.h"
#endif
class FEFontResource : public FEResourceHandle
{
public:
    void SetFontReference(nlFont* pFontReference);

#ifndef TARGET_PC
    /* 0x14 */ nlFont* m_pFontReference;
#else
    /* 0x14 */ port::SelfRelPtr32<nlFont> m_pFontReference;
#endif
};

#endif // _FEFONTRESOURCE_H_
