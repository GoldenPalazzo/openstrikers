list:
    @just --list

gen:
    @cmake -B build -G Ninja -DCMAKE_COLOR_DIAGNOSTICS=ON

build:
    @cmake --build build -j$(nproc)

show-err:
    @just build | grep --color=auto -i -B 2 -A 5 "error:"

show-link:
    @just build 2>&1 | grep "undefined reference to" | head -n 50

clean:
    @rm -rf build/

unpatch:
    @read -p "Checkout all submodules? [y/N] " ans; \
    if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then \
        git -C decomp checkout -- . || echo "FAILED: decomp"; \
        git -C decomp clean -fd || echo "FAILED: clean decomp"; \
        git -C decomp/extern/musyx checkout -- . || echo "FAILED: musyx"; \
        git -C decomp/extern/musyx clean -fd || echo "FAILED: clean musyx"; \
        git -C aurora checkout -- . || echo "FAILED: aurora"; \
        git -C aurora clean -fd || echo "FAILED: clean aurora"; \
    else \
        exit 1; \
    fi

patch:
    @bash ./apply_patches.sh
    @cp decomp/include/NL/detail/nlFunctionPreProcTemplate.h decomp/include/NL/detail/nlFunction1PreProcTemplate.h
    @echo "Generated decomp/include/NL/detail/nlFunction1PreProcTemplate.h"
