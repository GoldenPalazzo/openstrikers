list:
    @just --list

gen:
    @cmake -B build -G Ninja -DCMAKE_COLOR_DIAGNOSTICS=ON

build:
    @cmake --build build -j$(nproc)

gen-dbg:
    @cmake -B build-dbg -G Ninja -DCMAKE_COLOR_DIAGNOSTICS=ON \
        -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Debug

build-dbg:
    @cmake --build build-dbg -j$(nproc)

show-err:
    @just build | grep --color=auto -i -B 2 -A 5 "error:"

show-err-dbg:
    @just build-dbg | grep --color=auto -i -B 2 -A 5 "error:"

show-link:
    @just build 2>&1 | grep "undefined reference to" | head -n 50

clean:
    @rm -rf build/

unpatch:
    @read -p "Checkout all submodules? [y/N] " ans; \
    if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then \
        git -C extern/decomp checkout -- . || echo "FAILED: decomp"; \
        git -C extern/decomp clean -fd || echo "FAILED: clean decomp"; \
        git -C extern/decomp/extern/musyx checkout -- . || echo "FAILED: musyx"; \
        git -C extern/decomp/extern/musyx clean -fd || echo "FAILED: clean musyx"; \
        git -C extern/aurora checkout -- . || echo "FAILED: aurora"; \
        git -C extern/aurora clean -fd || echo "FAILED: clean aurora"; \
    else \
        exit 1; \
    fi

patch:
    @bash ./apply_patches.sh
    @cp extern/decomp/include/NL/detail/nlFunctionPreProcTemplate.h extern/decomp/include/NL/detail/nlFunction1PreProcTemplate.h
    @echo "Generated extern/decomp/include/NL/detail/nlFunction1PreProcTemplate.h"
