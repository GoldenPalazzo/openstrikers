#include <aurora/main.h>   // DEVE venire prima della tua definizione di main,
                            // altrimenti la macro non si applica e hai un
                            // vero secondo main() -> conflitto di link
#include <aurora/aurora.h>
#include <dolphin/gx/GXAurora.h>
#include <aurora/dvd.h>
#include "compat_shims.h"

int game_main(); // dichiarato qui, definito nel decomp rinominato

static const char* disc_path(int argc, char* argv[]) {
  if (argc > 1) {
    return argv[1];
  }
  return nullptr;
}

int main(int argc, char* argv[])   // <-- diventa aurora_main via macro
{
    const char* disc;
    disc = disc_path(argc, argv);
    const AuroraConfig config = {
        .appName = "openstrikers",
        .vsync = false,
        .startFullscreen = false,
        .allowTextureDumps = false,
        .mem1Size = 128 * 1024 * 1024,
        .mem2Size = ARAM_DEFAULT_SIZE,
    };
    const AuroraInfo info = aurora_initialize(argc, argv, &config);
    AuroraSetViewportPolicy(AURORA_VIEWPORT_FIT);
    // AuroraSetDisplayAspect(4/3);
    if (!aurora_dvd_open(disc)) {
        fprintf(stderr, "openstrikers: failed to open disc image %s\n", disc);
        aurora_shutdown();
        return 1;
    }
    return game_main();
}
