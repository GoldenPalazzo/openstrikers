#include "Game/AI/AISandbox.h"
#include "Game/AI/Scripts/ScriptCaching.h"
#include "Game/AI/Scripts/ScriptQuestions.h"

#ifndef TARGET_PC
template <>
AISandbox* nlSingleton<AISandbox>::s_pInstance = NULL;
#endif
