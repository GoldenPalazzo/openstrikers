#include "types.h"
#include "NL/nlBind.h"
#include "NL/nlFunction.h"
#include "Game/main.h"
#include "Game/Audio/AudioStream.h"
#include "Game/Sys/audio.h"
#include "Game/Sys/clock.h"
#include "NL/gl/glView.h"
#include "NL/gl/glTexture.h"
#include "NL/gl/glState.h"
#include "NL/gl/gl.h"
#include "NL/gl/glAppAttach.h"
#include "NL/gl/glMemory.h"
#include "Game/Effects/ParticleSystem.h"
#include "Game/Transitions/ModelTransition.h"
#include "NL/nlConfig.h"
#include "NL/nlMain.h"
#include "NL/nlFileGC.h"
#include "NL/nlLocalization.h"
#include "NL/nlString.h"
#include "NL/platpad.h"
#include "Game/ProfileTask.h"
#include "Game/Sys/FloatingPointExceptions.h"
#include "Game/Sys/CallStackDumper.h"
#include "Game/Sys/eventman.h"
#include "Game/Sys/gcmemcard.h"
#include "Game/Sys/debug.h"
#include "Game/Audio/AudioLoader.h"
#include "Game/Audio/AudioEventHandler.h"
#include "Game/Audio/CrowdMood.h"
#include "Game/FE/LidOpenMessage.h"
#include "Game/FE/FEAudio.h"
#include "Game/FE/feInput.h"
#include "Game/FE/feManager.h"
#include "Game/BeginFrameTask.h"
#include "Game/DispatchEventsTask.h"
#include "Game/PlatPadUpdateTask.h"
#include "Game/FixedUpdateTask.h"
#include "Game/WorldUpdateTask.h"
#include "Game/GameRenderTask.h"
#include "Game/FrontEndTask.h"
#include "Game/ParticleUpdateTask.h"
#include "Game/TweakerTask.h"
#include "Game/EndFrameTask.h"
#include "Game/TransitionTask.h"
#include "Game/ComUpdateTask.h"
#include "Game/TestTask.h"
#include "Game/Loader/LoadingManager.h"
#include "Game/GL/GLInventory.h"
#include "Game/Debug/ShapeRender.h"
#include "Game/Debug/FrameCounter.h"
#include "Game/GameInfo.h"
#include "Game/DB/StatsTracker.h"
#include "Game/DB/SaveLoad.h"
#include "Game/Render/Wiper.h"
#include "Game/Render/depthoffield.h"
#include "Game/Render/FlareHandler.h"
#include "Game/AI/AIPad.h"
#include "Game/OverlayManager.h"
#include "Game/PadActions.h"
#include "Game/Pad/FlickDetection.h"
#include "Game/Replay.h"
#include "Game/ReplayManager.h"
#include "Game/ReplayChoreo.h"
#include "Game/NisPlayer.h"
#include "Game/Render/Presentation.h"
#include "Game/Render/CrowdManager.h"
#include "Game/ResetTask.h"
#include "NL/nlDebug.h"
#include "NL/nlTask.h"
#include "dolphin/os/OSThread.h"
#include "dolphin/si.h"
#include "dolphin/card.h"

class AudioUpdateTask : public nlTask
{
public:
    /**
     * Offset/Address/Size: 0x1BB4 | 0x801750C4 | size: 0x8
     */
    virtual const char* GetName() { return "Audio"; }
    /**
     * Offset/Address/Size: 0x1BBC | 0x801750CC | size: 0x20
     */
    virtual void Run(float dt)
    {
        Audio::Update(dt);
    }
};

class ClockUpdateTask : public nlTask
{
public:
    /**
     * Offset/Address/Size: 0x1BDC | 0x801750EC | size: 0x8
     */
    virtual const char* GetName() { return "Clock"; }
    /**
     * Offset/Address/Size: 0x1BE4 | 0x801750F4 | size: 0x20
     */
    virtual void Run(float dt)
    {
        ClockManager::Update(dt);
    }
};

bool g_bProfiling = false;
bool g_bTweaking = false;
bool g_e3_Build = false;
bool g_Europe = false;
bool g_bFranticPausing = false;
nlLocalization::nlLanguage g_Language = nlLocalization::LangEnglish;
LoadingManager* g_pTheLoadingManagerTask = nullptr;

FrameCounter g_FrameCounter("frame", "send");

static ComUpdateTask comUpdateTask;
static TransitionTask transitionTask;
static DispatchEventsTask dispatchEventsTask;
static PlatPadUpdateTask platPadUpdateTask;
static FrontEndTask frontEndTask;
static WorldUpdateTask worldUpdateTask;
static GameRenderTask gameRenderTask;
static ParticleUpdateTask particleUpdateTask;
static ClockUpdateTask clockUpdateTask;
static BeginFrameTask beginFrameTask;
static AudioUpdateTask audioUpdateTask;
static EndFrameTask endFrameTask;
static TweakerTask tweakerTask;
static FixedUpdateTask fixedUpdateTask;

static TestTask testTask;
static ResetTask resetTask;

static void Initialize();
static void SetupViews();
static void AddTasks();
static void PreInitFS();
static void DoMemCheck();

/**
 * Offset/Address/Size: 0x1BAC | 0x801750BC | size: 0x8
 */
const int* GetRegion()
{
#if defined(VERSION_G4QJ01)
    static const int g_Region = 2;
#elif defined(VERSION_G4QP01)
    static const int g_Region = 1;
#else
    static const int g_Region = 0;
#endif
    return &g_Region;
}

static void PreInitFS()
{
}

/**
 * Offset/Address/Size: 0x354 | 0x80173864 | size: 0x1858
 */
static void Initialize()
{
    nlRegHandleDVDMessageCB(Function<void(int)>(DisplayDVDMessageSebring));
    nlRegHandleDVDAllClearCB(Function<void(int)>(DVDAllClearSebring));
    nlRegCheckForResetFromFSCB(Function<FnVoidVoid>(
        Bind<void>(MemFun<ResetTask, void>(&ResetTask::FSCheckForReset), &resetTask)));

    nlInit();
    bool glStartupSuccessful = glStartup();
    if (!glStartupSuccessful)
    {
        nlBreak();
    }
    nlSetRandomSeed(OSGetTick(), &nlDefaultSeed);
    bool globalTexturesLoaded = glLoadTextureBundle("global.glt");
    if (!globalTexturesLoaded)
    {
        nlBreak();
    }

    Config::Global().LoadFromFile("common.ini");
    Config::Global().LoadFromFile("platform.ini");
    Config::Global().LoadFromFile("locale.ini");
    Config::Global().LoadFromFile("user.ini");

    GetConfigBool(Config::Global(), "DiskAccess", false);
    if (GetConfigBool(Config::Global(), "e3_build", false))
    {
        g_e3_Build = true;
    }
    if (GetConfigBool(Config::Global(), "frantic_pausing", false))
    {
        g_bFranticPausing = true;
    }

    g_bFrameSmiler = GetConfigBool(Config::Global(), "Frame_Smiler", false);
    g_bFrameStatsOnScreen = GetConfigBool(Config::Global(), "Frame_Stats_On_Screen", false);
    g_bFrameStatsOnDisk = GetConfigBool(Config::Global(), "Frame_Stats_On_Disk", false);
    g_bRunSimAndRenderInLockStep = GetConfigBool(Config::Global(), "lockstep", false);

    EventManager::Create(128, 64);
    g_pEventManager->AddEventHandler(FrontEnd::FEEventHandler, NULL, 2);
    g_pEventManager->AddEventHandler(OverlayManager::FEEventHandler, NULL, (u32)-1);
    g_pEventManager->AddEventHandler(FEAudioEventHandler, NULL, 2);
    g_pEventManager->AddEventHandler(Audio::AudioEventHandler, NULL, 0x16);

    nlTaskManager::Startup(0x10000);
    tDebugPrintManager::Initialize();
    ClockManager::Initialize();

    AudioLoader::gbDisableAudio = 
#ifndef GOLDEN_DISABLE_AUDIO
        GetConfigBool(Config::Global(), "no_audio", false);
#else
    true;
#endif
    AudioLoader::gbStream = !GetConfigBool(Config::Global(), "no_stream", false);
    AudioLoader::g_BGM_Off = GetConfigBool(Config::Global(), "no_bgm", false);
    AudioLoader::gbDisableCrowd = GetConfigBool(Config::Global(), "no_crowd", false);
    AudioLoader::gbDisableReverb = GetConfigBool(Config::Global(), "no_reverb", false);

    CrowdMood::ReadConfig();

    if (!AudioLoader::gbDisableAudio)
    {
        AudioLoader::Initialize();
        AudioLoader::SetupSoundBuffers();
        AudioLoader::LoadFEButtonSoundGroup();
        Audio::InitStreaming();
    }

    g_pEventManager->AddEventHandler(ReplayManager::EventHandler, ReplayManager::Instance(), (u32)-1);
    g_pEventManager->AddEventHandler(ReplayChoreo::EventHandler, &ReplayChoreo::Instance(), (u32)-1);
    g_pEventManager->AddEventHandler(NisPlayer::EventHandler, NisPlayer::Instance(), (u32)-1);
    g_pEventManager->AddEventHandler(Presentation::EventHandler, &Presentation::Instance(), (u32)-1);
    g_pEventManager->AddEventHandler(CrowdManager::EventHandler, &CrowdManager::instance, (u32)-1);

    glResourceMark();
    glInventory.Create();
    InitPads();
    SISetSamplingRate(0);
    PADSetSamplingCallback(VBlankPadUpdate);
    AIPadManager::Startup();
    FEInput::Initialize();
    FlickDetection::Initialize();
    CARDInit("G4QE", "01");
    MemCard::s_InitDone = true;

    g_pTheLoadingManagerTask = new (nlMalloc(sizeof(LoadingManager), 8, false)) LoadingManager(0x14);

    if (!GetConfigBool(Config::Global(), "DisableComListener", false))
    {
        comUpdateTask.Initialize();
    }

    TransitionTask::sm_pGlobalTask = &transitionTask;
    transitionTask.Initialize(*g_pTheLoadingManagerTask);

    testTask.Initialize();
    nlLocalization::Initialize();

    DVDDiskID* diskid = DVDGetCurrentDiskID();
    if (diskid->gameName[0] == 'G' && diskid->gameName[1] == '4' && diskid->gameName[2] == 'Q' && diskid->gameName[3] == 'P')
    {
        switch (OSGetLanguage())
        {
        case 1:
            g_Language = nlLocalization::LangGerman;
            break;
        case 2:
            g_Language = nlLocalization::LangFrench;
            break;
        case 3:
            g_Language = nlLocalization::LangSpanish;
            break;
        case 4:
            g_Language = nlLocalization::LangItalian;
            break;
        default:
            g_Language = nlLocalization::LangUKEnglish;
            break;
        }
        g_Europe = true;
    }
    else if (diskid->gameName[0] == 'G' && diskid->gameName[1] == '4' && diskid->gameName[2] == 'Q' && diskid->gameName[3] == 'J')
    {
        g_Language = nlLocalization::LangJapanese;
    }
    else if (diskid->gameName[0] == 'G' && diskid->gameName[1] == '4' && diskid->gameName[2] == 'Q' && diskid->gameName[3] == 'E')
    {
        g_Language = nlLocalization::LangEnglish;
    }
    else
    {
        BasicString<char, Detail::TempStringAllocator> userlanguage = Config::Global().Get<BasicString<char, Detail::TempStringAllocator> >(
            "Language", BasicString<char, Detail::TempStringAllocator>("eng"));

        if (nlStrICmp(userlanguage.c_str(), "eng") == 0)
        {
            g_Language = nlLocalization::LangEnglish;
        }
        else if (nlStrICmp(userlanguage.c_str(), "jpn") == 0)
        {
            g_Language = nlLocalization::LangJapanese;
        }
        else if (nlStrICmp(userlanguage.c_str(), "deu") == 0)
        {
            g_Language = nlLocalization::LangGerman;
        }
        else if (nlStrICmp(userlanguage.c_str(), "fre") == 0)
        {
            g_Language = nlLocalization::LangFrench;
        }
        else if (nlStrICmp(userlanguage.c_str(), "ita") == 0)
        {
            g_Language = nlLocalization::LangItalian;
        }
        else if (nlStrICmp(userlanguage.c_str(), "spa") == 0)
        {
            g_Language = nlLocalization::LangSpanish;
        }
        else if (nlStrICmp(userlanguage.c_str(), "uke") == 0)
        {
            g_Language = nlLocalization::LangUKEnglish;
        }
        else if (nlStrICmp(userlanguage.c_str(), "longest") == 0)
        {
            g_Language = nlLocalization::LangLongestStrings;
        }
    }

    LoadMemoryCardIconData();

    if (nlSingleton<GameInfoManager>::s_pInstance == NULL)
    {
        nlSingleton<GameInfoManager>::s_pInstance = new (nlMalloc(sizeof(GameInfoManager), 8, false)) GameInfoManager();
    }
    if (nlSingleton<StatsTracker>::s_pInstance == NULL)
    {
        nlSingleton<StatsTracker>::s_pInstance = new (nlMalloc(sizeof(StatsTracker), 8, false)) StatsTracker();
    }

    AddTasks();

    SetupViews();
    g_ShapeRenderer.Initialize();
    Wiper::Instance().Initialize();
    DepthOfFieldManager::instance.Initialize();
    FlareHandler::instance.Initialize();
    glAppStartup();

    BasicString<char, Detail::TempStringAllocator> skinString = Config::Global().Get<BasicString<char, Detail::TempStringAllocator> >("Skinning", BasicString<char, Detail::TempStringAllocator>("both"));
    BasicString<char, Detail::TempStringAllocator> replaySkin = Config::Global().Get<BasicString<char, Detail::TempStringAllocator> >("UserReplaySkinning", BasicString<char, Detail::TempStringAllocator>("blend"));
    if (skinString == "both")
    {
        BeginFrameTask::s_GameplaySkin = eModelSkin_Both;
    }
    else if (skinString == "rigid")
    {
        BeginFrameTask::s_GameplaySkin = eModelSkin_Rigid;
    }
    else
    {
        BeginFrameTask::s_GameplaySkin = eModelSkin_Blend;
    }
    if (replaySkin == "both")
    {
        BeginFrameTask::s_ReplaySkin = eModelSkin_Both;
    }
    else if (replaySkin == "rigid")
    {
        BeginFrameTask::s_ReplaySkin = eModelSkin_Rigid;
    }
    else
    {
        BeginFrameTask::s_ReplaySkin = eModelSkin_Blend;
    }
}

static void AddTasks()
{
    nlTaskManager::AddTask(&resetTask, 0, -1);
    nlTaskManager::AddTask(&beginFrameTask, 2, -1);
    nlTaskManager::AddTask(&dispatchEventsTask, 0x14, -1);
    nlTaskManager::AddTask(&platPadUpdateTask, 3, -1);
    nlTaskManager::AddTask(&clockUpdateTask, 5, -1);
    nlTaskManager::AddTask(&fixedUpdateTask, 7, -1);
    nlTaskManager::AddTask(&worldUpdateTask, 8, 0x20013);
    nlTaskManager::AddTask(&gameRenderTask, 0xa, 0x20113);
    nlTaskManager::AddTask(&frontEndTask, 0xc, 0x117);
    nlTaskManager::AddTask(&particleUpdateTask, 0xb, 0x20113);
    nlTaskManager::AddTask(&tweakerTask, 0xd, -1);
    nlTaskManager::AddTask(&audioUpdateTask, 0xe, -1);
    nlTaskManager::AddTask(&endFrameTask, 0xf, -1);
    nlTaskManager::AddTask(&transitionTask, 1, -1);
    nlTaskManager::AddTask(g_pTheLoadingManagerTask, 6, -1);

    if (!GetConfigBool(Config::Global(), "DisableComListener", false))
    {
        nlTaskManager::AddTask(&comUpdateTask, 0x10, -1);
    }
    if (GetConfigBool(Config::Global(), "test/enable", false))
    {
        nlTaskManager::AddTask(&testTask, 0x12, -1);
    }
}

/**
 * Offset/Address/Size: 0x224 | 0x80173734 | size: 0x130
 */
static void SetupViews()
{
    static eGLView sort_none[] = {
        GLV_Shadow0, GLV_Shadow1, GLV_UnsortedPerspective, GLV_InvisiblePlane, GLV_ElectricFence, GLV_UnsortedOrtho, GLV_ShadowBlend0, GLV_ShadowBlend1, GLV_Debug, GLV_Transitions, GLV_CoPlanar0, GLV_CoPlanar
    };

    static eGLView disabled_views[] = {
        GLV_ShadowBlend0, GLV_ShadowBlend1, GLV_ScreenBlur, GLV_ScreenBlur2
    };

    for (int iview = 0; iview < GLV_Num; iview++)
    {
        glViewSetTarget((eGLView)iview, GLTG_Main);
    }

    glViewSetSortMode(GLV_FrontEnd, GLVSort_TransformedDepth);
    glViewSetSortMode(GLV_Anark, GLVSort_Reverse);

    for (int iview = 0; iview < sizeof(sort_none) / sizeof(eGLView); iview++)
    {
        glViewSetSortMode(sort_none[iview], GLVSort_None);
    }

    for (int iview = 0; iview < sizeof(disabled_views) / sizeof(eGLView); iview++)
    {
        glViewSetEnable(disabled_views[iview], false);
    }

    u32 uWarbleTexture = glGetTexture("target/warble");
    bool bWarbleLoaded = glTextureLoad(uWarbleTexture);
    if (!bWarbleLoaded)
    {
        glViewSetEnable(GLV_Warble, false);
        glViewSetEnable(GLV_WarbleBlend, false);
    }

    glViewSetDepthClear(GLV_CameraSpace, true);
    glViewSetDepthClear(GLV_Transitions, true);
    glViewSetDepthClear(GLV_Transitions3D, true);
    glViewSetDepthClear(GLV_Anark3D_BG, true);
    glViewSetDepthClear(GLV_Anark3D_FG, true);

    ParticleSystem::ClearViews();
    ParticleSystem::AddView(GLV_Particles);

    ModeledScreenTransition::s_3DView = GLV_Transitions3D;
}

static void DoMemCheck()
{
}

/**
 * Offset/Address/Size: 0x0 | 0x80173510 | size: 0x224
 */
int game_main()
{
    if (g_DoStackWatermarkTests)
    {
        OSClearStack(g_StackWatermarkFiller);
    }

    Initialize();

    fopen("flushfile.txt", "r");

    nlTaskManager::SetNextState(GetConfigBool(Config::Global(), "skipfe", false) ? 2 : 4);

    if (GetConfigBool(Config::Global(), "enableFloatingPointExceptions", false))
    {
        // InstallFloatingPointExceptionHandler();
    }

    if (GetConfigBool(Config::Global(), "callStackDumper", false))
    {
        // InstallCallStackDumper();
    }

    for (;;)
    {
        nlTaskManager::RunAllTasks();
        UpdateProfile();
    }
}
