#include "compat_shims.h"

// #include <cerrno>
#include <cstdarg>

extern "C" int __float_max[] = { 0x7F7FFFFF };
extern "C" float __float_min[] = { 0x00800000 };
extern "C" int __float_nan[] = { 0x7FFFFFFF };
extern "C" int __float_huge[] = { 0x7F800000 };

// GX render mode stub
extern "C" GXRenderModeObj GXNtsc480Prog = {};
// MSL __lower_map (case conversion table)

extern "C" const unsigned short __lower_map[256] = {
    0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0A,0x0B,0x0C,0x0D,0x0E,0x0F,
    0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x17,0x18,0x19,0x1A,0x1B,0x1C,0x1D,0x1E,0x1F,
    0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2A,0x2B,0x2C,0x2D,0x2E,0x2F,
    0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x3A,0x3B,0x3C,0x3D,0x3E,0x3F,
    0x40,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6A,0x6B,0x6C,0x6D,0x6E,0x6F,
    0x70,0x71,0x72,0x73,0x74,0x75,0x76,0x77,0x78,0x79,0x7A,0x5B,0x5C,0x5D,0x5E,0x5F,
    0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6A,0x6B,0x6C,0x6D,0x6E,0x6F,
    0x70,0x71,0x72,0x73,0x74,0x75,0x76,0x77,0x78,0x79,0x7A,0x7B,0x7C,0x7D,0x7E,0x7F,
    0x80,0x81,0x82,0x83,0x84,0x85,0x86,0x87,0x88,0x89,0x8A,0x8B,0x8C,0x8D,0x8E,0x8F,
    0x90,0x91,0x92,0x93,0x94,0x95,0x96,0x97,0x98,0x99,0x9A,0x9B,0x9C,0x9D,0x9E,0x9F,
    0xA0,0xA1,0xA2,0xA3,0xA4,0xA5,0xA6,0xA7,0xA8,0xA9,0xAA,0xAB,0xAC,0xAD,0xAE,0xAF,
    0xB0,0xB1,0xB2,0xB3,0xB4,0xB5,0xB6,0xB7,0xB8,0xB9,0xBA,0xBB,0xBC,0xBD,0xBE,0xBF,
    0xC0,0xC1,0xC2,0xC3,0xC4,0xC5,0xC6,0xC7,0xC8,0xC9,0xCA,0xCB,0xCC,0xCD,0xCE,0xCF,
    0xD0,0xD1,0xD2,0xD3,0xD4,0xD5,0xD6,0xD7,0xD8,0xD9,0xDA,0xDB,0xDC,0xDD,0xDE,0xDF,
    0xE0,0xE1,0xE2,0xE3,0xE4,0xE5,0xE6,0xE7,0xE8,0xE9,0xEA,0xEB,0xEC,0xED,0xEE,0xEF,
    0xF0,0xF1,0xF2,0xF3,0xF4,0xF5,0xF6,0xF7,0xF8,0xF9,0xFA,0xFB,0xFC,0xFD,0xFE,0xFF
};

extern "C" unsigned char __ctype_map[256] = {0};

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

void VISetBlack(int) {}
void VIWaitForRetrace() {}

u32 VIGetRetraceCount() { return 0; }
void VISetNextFrameBuffer(void*) {}
VIRetraceCallback VISetPreRetraceCallback(VIRetraceCallback) { return NULL; }
VIRetraceCallback VISetPostRetraceCallback(VIRetraceCallback cb) { return NULL; }
u32 VIGetDTVStatus() { return 0; }



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
 
void OSRestoreInterrupts(BOOL state) {
    (void)state;
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
