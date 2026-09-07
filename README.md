# openstrikers
<!-- [![Discord Badge]][discord] -->
<!---->
<!-- [Discord Badge]: https://img.shields.io/discord/727908905392275526?color=%237289DA&logo=discord&logoColor=%23FFFFFF -->
<!-- [discord]: https://discord.gg/hKx3FJJgrV -->

A porting of Super Mario Strikers, the GameCube game, for modern platforms.

This repository does **not** contain any game assets or assembly whatsoever.
An existing copy of the game is required.

Based on the [decompilation](https://github.com/yannicksuter/smstrikers-decomp)
by [@yannicksuter](https://github.com/yannicksuter).

## Legal status and licensing

This repository aims at applying patches to an already existing source
reconstruction in any way not affiliated with, not authorized by, not
sponsored by nor endorsed by Nintendo or Next Level Games.

The decompilation is, as already stated, a reconstruction via reverse
engineering and not a source-code release.

There isn't a single license for the entire repo. The decomp itself is
distributed with all the licenses of each individual component and their
CC0 1.0 license (see [`decomp/LICENSE`](extern/decomp/LICENSE) and
[](extern/decomp/LICENSE.txt)).

[](https://github.com/encounter/aurora) ships with its own MIT license
(see [](extern/aurora/LICENSE)).

## Building from source

### Prerequisites

Currently, the only tested environment is Linux (specifically NixOS).

It's recommended to use [nix](https://nix.dev/install-nix) as package manager
to use the [`flake.nix`](flake.nix) provided with repo and install with ease
all project's dependencies

### Build

To build in a fresh copy of the repo:

```bash
# if you have just installed
just patch gen build
# else
bash ./apply_patches.sh
cp extern/decomp/include/NL/detail/nlFunctionPreProcTemplate.h \
    extern/decomp/include/NL/detail/nlFunction1PreProcTemplate.h
cmake -B build -G Ninja -DCMAKE_COLOR_DIAGNOSTICS=ON
cmake --build build -j$(nproc)
```

To update a build:

```bash
just build
# or, if you haven't installed just
cmake --build build -j$(nproc)
```

If you need to checkout all `extern` repos for whatever reason:

```bash
just unpatch
# or, the extremely verbose bash equivalent
git -C extern/decomp checkout -- .
git -C extern/decomp clean -fd
git -C extern/decomp/extern/musyx checkout -- .
git -C extern/decomp/extern/musyx clean -fd
git -C extern/aurora checkout -- .
git -C extern/aurora clean -fd
```

### Debug build

When you're in the `cmake -B build` phase, run this

```bash
cmake -B build-dbg -G Ninja -DCMAKE_COLOR_DIAGNOSTICS=ON \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Debug
# if you have just, you can *just* run
just gen-dbg build-dbg
```

It will also come with `compile_commands.json` for eventual language servers.

## Contributing

Contribute freely to both this repo and the
[decomp's fork](https://github.com/GoldenPalazzo/smstrikers-decomp) on branch
`port-x86_64`.

To talk about the decomp, join the
[GC/Wii decomps Discord server](https://discord.gg/hKx3FJJgrV) and chat in
`#super-mario-strikers`.

A discord group for the porting is in the work.
