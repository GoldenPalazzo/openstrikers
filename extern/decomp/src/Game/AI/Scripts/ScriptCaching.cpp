#include "Game/AI/Scripts/ScriptCaching.h"

unsigned char g_bScriptQuestionCachingOn = 1;
unsigned char g_bScriptQuestionCachingUseSTD;
template <>
ScriptQuestionCache* nlSingleton<ScriptQuestionCache>::s_pInstance = 0;
