#ifndef _FEPACKAGE_H_
#define _FEPACKAGE_H_

#include "Game/FE/fePresentation.h"
#include "port/endian.h"

class FELibObject;
class FEResourceHandle;
class TLComponent;

class FEPackage
{
public:
    void Update(float deltaTime);
    FEPresentation* GetPresentation() const;

    /* 0x00 */ port::SelfRelPtr32<TLComponent> m_pComponentList;
    /* 0x04 */ port::SelfRelPtr32<FEPresentation> m_pFEPresentation;
    /* 0x08 */ port::SelfRelPtr32<FEResourceHandle> m_pResourceList;
    /* 0x0C */ port::SelfRelPtr32<FELibObject> m_pFEObjectLibrary;
    /* 0x10 */ port::be<u32> m_uUniqueID;
    /* 0x14 */ port::be<u32> m_uResourceCount;
}; // total size: 0x18

#endif // _FEPACKAGE_H_
