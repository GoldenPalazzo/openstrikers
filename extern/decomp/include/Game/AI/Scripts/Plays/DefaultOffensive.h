#ifndef _DEFAULTOFFENSIVE_H_
#define _DEFAULTOFFENSIVE_H_

#include "Game/AI/DecisionEntity.h"
#include "Game/AI/Fielder.h"
#include "Game/AI/FuzzyVariant.h"
#include "Game/Team.h"

class cPlayer;

class Fuzzy
{
public:
    static FuzzyVariant AbortOffensivePlay(cDecisionEntity* pDecision);
    static FuzzyVariant DefaultOffensivePlay(cDecisionEntity* pDecision);
    static FuzzyVariant DoPassing(float fConfidence, cDecisionEntity* pDecision);
    static FuzzyVariant GetBestPassTarget(cPlayer*);
    static FuzzyVariant GetStrategicBallCarrier(cTeam*);
    static FuzzyVariant GoodBallCarrier(cFielder* TheFielder);
    static FuzzyVariant GoodToShoot(cFielder*);
    static FuzzyVariant GoodToChipShot(cFielder*);
    static FuzzyVariant InGoodWindupPosition(cFielder* TheFielder);
    static FuzzyVariant InDanger(cFielder*);
    static FuzzyVariant CutAndBreak(cFielder* TheFielder);
    static FuzzyVariant DoShooting(float fConfidence, cDecisionEntity* pDecision);
    static FuzzyVariant FurthestBackOnMyTeam(cFielder* TheFielder);
    static FuzzyVariant UsePowerupOffensive(float fConfidence, cDecisionEntity* pDecision);
    static FuzzyVariant GetPowerupTargetOffensive(cTeam* TheTeam);
    static FuzzyVariant InDangerDelayed(cFielder*);
};

#endif // _DEFAULTOFFENSIVE_H_
