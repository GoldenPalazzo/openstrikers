#ifndef _EMISSIONCONTROLLER_H_
#define _EMISSIONCONTROLLER_H_

#include "NL/nlMath.h"
#include "NL/nlFunction.h"
#include "NL/gl/gl.h"

#include "Game/Effects/EffectsGroup.h"
#include "Game/Effects/efList.h"

template <typename T>
struct ReplayFrameTraits;

class LoadFrame;

class cPN_SAnimController;
class cPoseAccumulator;
class EmissionController;
typedef void FnEmissionController(EmissionController&);

void* fxLoadEntireFileHigh(const char* filename, u32* fileSize);

class EmissionController : public efNode
{
public:
    EmissionController(EffectsGroup* pEffectsGroup, unsigned short id, eGLView view);
    ~EmissionController();
    void InitializeSystemsFromGroup();
    void SetPosition(const nlVector3& pos);
    const nlVector3& GetPosition() const;
    void SetDirection(const nlVector3& dir);
    void SetVelocity(const nlVector3& velocity);
    void SetPoseAccumulator(const cPoseAccumulator& pose);
    void SetAnimController(const cPN_SAnimController& animController);
    void Die();
    float GetRemainingTime() const;
    bool IsLingering() const;
    bool Update(float dt);
    void Render();
    void SetUpdateCallback(const Function1<void, EmissionController&>& callback);
    void SetFinishedCallback(const Function1<void, EmissionController&>& callback);

    template <typename T>
    void Replay(T& frame);

    /* 0x8, */ EffectsGroup* m_pGroup;
    /* 0xC, */ efList m_Systems;
    /* 0x18 */ Function1<void, EmissionController&> mUpdateCallback;
    /* 0x20 */ Function1<void, EmissionController&> mFinishedCallback;
    /* 0x28 */ s8 m_GlView;
    /* 0x29 */ bool m_Replaying;
    /* 0x2C */ f32 m_Age;
    /* 0x30 */ f32 m_ReplayDeltaTime;
    /* 0x34 */ f32 m_fGround;
    /* 0x38 */ u16 m_aFacing;
    /* 0x3A */ bool m_bVisible;
    /* 0x3B */ bool m_bDisabled;
    /* 0x3C */ nlVector3 m_Mirror;
    /* 0x48 */ nlVector3 m_vPosition;
    /* 0x54 */ nlVector3 m_vDirection;
    /* 0x60 */ nlVector3 m_vVelocity;
    /* 0x6C */ const cPoseAccumulator* m_pPose;
    /* 0x70 */ const cPN_SAnimController* m_pAnimController;
    /* 0x74 */ u16 m_Id;
    /* 0x78 */ u32 m_uUserData;
    /* 0x7C */ u32 m_uJointIDOverride;
    /* 0x80 */ s32 m_nUserEffects;
    /* 0x84 */ UserEffectSpec** m_pUserEffects;
    /* 0x88 */ bool m_bPoseErrorDisplayed;
};

#endif // _EMISSIONCONTROLLER_H_
