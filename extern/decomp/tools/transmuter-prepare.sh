#!/bin/bash
# Prepare a Melee TU for `transmuter match`.
#
# Generates the preprocessed `.ctx` for a source file (via ninja) and copies
# it to a `.ctx.c` so mwcc and Transmuter both accept the extension.
# Then prints the suggested `transmuter match` invocation, including
# `--isolate` so Transmuter strips non-target bodies and #defines before the
# search starts.
#
# Usage: tools/transmuter-prepare.sh <src/path/to/file.c> <function_name>
#
# Example:
#   tools/transmuter-prepare.sh src/melee/if/iftime.c ifTime_GetCountdownSeconds

set -e

SRC="$1"
FN="$2"

if [ -z "$SRC" ] || [ -z "$FN" ]; then
    echo "usage: $0 <src/path/to/file.cpp> <function_name>" >&2
    exit 2
fi

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

if [ ! -f "$SRC" ]; then
    echo "error: source file not found: $SRC" >&2
    exit 1
fi

# Map src/melee/if/iftime.c → build/GALE01/src/melee/if/iftime
case "$SRC" in
    src/*) ;;
    *) echo "error: source must live under src/, got: $SRC" >&2; exit 1 ;;
esac
BASE="build/G4QE01/${SRC%.cpp}"
CTX="$BASE.ctx"
CTX_C="$BASE.ctx.cpp"
TARGET_O="build/G4QE01/obj/${SRC#src/}"
TARGET_O="${TARGET_O%.cpp}.o"

if [ ! -f "$TARGET_O" ]; then
    echo "error: target object not found: $TARGET_O" >&2
    echo "       (run \`ninja\` first to extract it from the ROM split)" >&2
    exit 1
fi

echo ">> ninja $CTX"
ninja "$CTX"

# Copy is cheap and keeps the .ctx around for re-use; use cp -f so we
# always reflect the latest ninja output.
echo ">> cp $CTX -> $CTX_C"
cp -f "$CTX" "$CTX_C"

# Locate the transmuter binary. Allow override via $TRANSMUTER, otherwise
# look at the conventional checkout next to the melee repo.
TRANSMUTER_BIN="${TRANSMUTER:-$REPO/../transmuter/packages/cli/dist/index.js}"
if [ ! -f "$TRANSMUTER_BIN" ]; then
    echo "warn: transmuter CLI not found at $TRANSMUTER_BIN" >&2
    echo "      set \$TRANSMUTER to the absolute path of packages/cli/dist/index.js" >&2
    TRANSMUTER_BIN="<path-to-transmuter>/packages/cli/dist/index.js"
fi

cat <<EOF

Ready. To run the match:

    cd $REPO
    bun $TRANSMUTER_BIN match \\
        $CTX_C \\
        --target $TARGET_O \\
        --function $FN \\
        --compiler "tools/transmuter-compile.sh {{inputPath}} {{outputPath}}" \\
        --cwd "\$(pwd)" \\
        --concurrency $(nproc) \\
        --timeout 900000

Notes:
  - Reducer is enabled by default (no --no-reduce). On a large ctx it
    runs first to binary-search away unrelated code, after which the
    mutation engine works on a much smaller source. The reducer phase
    can take 1-3 minutes on large TUs but pays off afterwards. Pass
    --no-reduce for a quick smoke run.
  - --isolate is NOT used here. Our C++ ctx (with extern "C", classes,
    namespaces, decompctx.py-style annotations) trips Transmuter's
    isolation phase ("Initial compilation failed: Errors caused tool to
    abort"). Stick to the reducer for size reduction.
  - Default --timeout is 15 min. Override on the command line for
    longer runs (e.g. --timeout 1800000 for 30 min).
EOF

