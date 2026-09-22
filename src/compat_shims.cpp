#include "compat_shims.h"

// #include <cerrno>
#include <cstdarg>
#include <utility>

extern "C" int __float_max[] = { 0x7F7FFFFF };
extern "C" float __float_min[] = { 0x00800000 };
extern "C" int __float_nan[] = { 0x7FFFFFFF };
extern "C" int __float_huge[] = { 0x7F800000 };

// GX render mode stub
extern "C" GXRenderModeObj GXNtsc480Prog = {};
// MSL __lower_map (case conversion table)

extern "C" {

void C_MTX44Identity(Mtx44 m) {
    m[0][0] = 1.0f; m[0][1] = 0.0f; m[0][2] = 0.0f; m[0][3] = 0.0f;
    m[1][0] = 0.0f; m[1][1] = 1.0f; m[1][2] = 0.0f; m[1][3] = 0.0f;
    m[2][0] = 0.0f; m[2][1] = 0.0f; m[2][2] = 1.0f; m[2][3] = 0.0f;
    m[3][0] = 0.0f; m[3][1] = 0.0f; m[3][2] = 0.0f; m[3][3] = 1.0f;
}

void C_MTX44Concat(const Mtx44 a, const Mtx44 b, Mtx44 ab) {
    Mtx44 tmp;
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            tmp[i][j] = a[i][0]*b[0][j] + a[i][1]*b[1][j]
                      + a[i][2]*b[2][j] + a[i][3]*b[3][j];
        }
    }
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++)
            ab[i][j] = tmp[i][j];
}

void C_MTX44Transpose(const Mtx44 src, Mtx44 xPose) {
    Mtx44 tmp;
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++)
            tmp[j][i] = src[i][j];
    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++)
            xPose[i][j] = tmp[i][j];
}

void C_MTX44Scale(Mtx44 m, f32 xS, f32 yS, f32 zS) {
    C_MTX44Identity(m);
    m[0][0] = xS;
    m[1][1] = yS;
    m[2][2] = zS;
}

u32 C_MTX44Inverse(const Mtx44 src, Mtx44 inv) {
    f32 a[4][8];
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) a[i][j] = src[i][j];
        for (int j = 0; j < 4; j++) a[i][j+4] = (i == j) ? 1.0f : 0.0f;
    }

    for (int col = 0; col < 4; col++) {
        int pivot = col;
        f32 maxVal = fabsf(a[col][col]);
        for (int r = col + 1; r < 4; r++) {
            if (fabsf(a[r][col]) > maxVal) { maxVal = fabsf(a[r][col]); pivot = r; }
        }
        if (maxVal == 0) return 0;

        if (pivot != col) {
            for (int j = 0; j < 8; j++) std::swap(a[col][j], a[pivot][j]);
        }

        f32 d = a[col][col];
        for (int j = 0; j < 8; j++) a[col][j] /= d;

        for (int r = 0; r < 4; r++) {
            if (r == col) continue;
            f32 f = a[r][col];
            for (int j = 0; j < 8; j++) a[r][j] -= f * a[col][j];
        }
    }

    for (int i = 0; i < 4; i++)
        for (int j = 0; j < 4; j++)
            inv[i][j] = a[i][j+4];

    return 1;
}

// --- Cache / PPC stubs ---
void PPCSync() {}
void DCFlushRangeNoSync(void*, u32) {}
void DCStoreRangeNoSync(void*, u32) {}
void DCStoreRange(void*, u32) {}

void DCFlushRange(void*, u32) {}
void DCZeroRange(void*, u32) {}
void DCInvalidateRange(void*, u32) {}


// --- VI stubs ---

// --- OS stubs ---

void OSYieldThread() {}
u32 OSGetConsoleType() { return 0; }

u32 OSGetResetCode() { return 0; }
void OSResetSystem(int, u32, BOOL) {}
u32 OSGetSoundMode() { return 0; }

void OSSetSoundMode(u32) {}
u8 OSGetLanguage() { return 0; }
u32 OSGetProgressiveMode() { return 0; }

void OSSetProgressiveMode(u32) {}
u32 OSGetEuRgb60Mode() { return 0; }
void OSSetEuRgb60Mode(u32) {}

BOOL OSGetResetButtonState() { return 0; }
void OSClearStack(u8) {}

// --- GX stubs ---
void GXPeekARGB(u16, u16, u32* val) { *val = 0; }

void GXPokeColorUpdate(GXBool) {}
void GXPokeBlendMode(GXBlendMode, GXBlendFactor, GXBlendFactor, GXLogicOp) {}

void GXPokeARGB(u16, u16, u32) {}
f32 GXGetYScaleFactor(u16, u16) { return 1.0f; }

// --- VM stubs ---

void VMInit(uintptr_t baseAddr, size_t initialCommitSize, uintptr_t limitAddr) {}
void VMAlloc(uintptr_t address, size_t size) {}
void VMSetLogStatsCallback(VMLogStatsCallback cb) {}

void LCEnable() {}
void LCDisable() {}
 
BOOL THPInit() {
    return TRUE;
}
 

static void DummyAIDCallback() {}
 
void* AIRegisterDMACallback(void* callback) {
    (void)callback;
    static void* sPrevCallback = (void*)DummyAIDCallback;
    void* prev = sPrevCallback;
    sPrevCallback = callback ? callback : (void*)DummyAIDCallback;
    return prev;
}
 
void AIInitDMA(u32 addr, u32 size) {
    (void)addr;
    (void)size;
}
 
void AIStartDMA() {}
 
u32 AIGetDMAStartAddr() {
    return 0;
}
 
u32 AIGetDSPSampleRate() {
    return 0;
}
 
BOOL OSEnableInterrupts() {
    return TRUE;
}
 
BOOL OSDisableInterrupts() {
    return TRUE;
}
 
BOOL OSRestoreInterrupts(BOOL state) {
    return TRUE;
}

void OSReport(const char* msg, ...) {
    va_list args;
    va_start(args, msg);
    printf(msg, args);
    va_end(args);
}

#ifdef GOLDEN_DISABLE_AUDIO
u32 THPAudioDecode(void*, void*, long) { return 0; }
s32 THPVideoDecode(void* file, void* tileY, void* tileU, void* tileV, void* work) { return 0; }
#endif

} // extern "C"
