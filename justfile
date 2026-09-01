list:
    @just --list

gen:
    @cmake -B build -G Ninja -DCMAKE_COLOR_DIAGNOSTICS=ON

build:
    @cmake --build build -j$(nproc)

show-err:
    @just build | grep --color=auto -i -B 2 -A 5 "error:"

clean:
    @rm -rf build/

unpatch:
    @read -p "Checkout all submodules? [y/N] " ans; \
    if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then \
        git -C decomp checkout -- . || echo "FAILED: decomp"; \
        git -C decomp/extern/musyx checkout -- . || echo "FAILED: musyx"; \
        git -C aurora checkout -- . || echo "FAILED: aurora"; \
    else \
        exit 1; \
    fi

patch:
    @bash ./apply_patches.sh
