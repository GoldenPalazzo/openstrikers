#include "Game/AI/Scripts/ScriptCaching.h"

unsigned char g_bScriptQuestionCachingOn = 1;
unsigned char g_bScriptQuestionCachingUseSTD;
#ifndef TARGET_PC
template <>
ScriptQuestionCache* nlSingleton<ScriptQuestionCache>::s_pInstance = 0;
#endif
