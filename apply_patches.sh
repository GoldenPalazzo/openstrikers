#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
EXTERN_DIR="$ROOT/extern"
cd "$EXTERN_DIR"

for repo in decomp decomp/extern/musyx aurora; do
  if [ -n "$(git -C "$repo" status --porcelain)" ]; then
    echo "WARNING: $repo has edits that aren't saved as a patch. Aborting...."
    echo "Generate the missing patch with: git -C $repo diff > patches/.../name.patch"
    exit 1
  fi
done

echo "== reset decomp at clean HEAD =="
git -C decomp checkout -- .
git -C decomp clean -fd

echo "== reset musyx at clean HEAD =="
git -C decomp/extern/musyx checkout -- .
git -C decomp/extern/musyx clean -fd

echo "== reset aurora at clean HEAD =="
git -C aurora checkout -- .
git -C aurora clean -fd

echo "== applying decomp patches =="
for p in "$ROOT"/patches/decomp/*.patch; do
  [ -e "$p" ] || continue
  echo "-> $p"
  git -C decomp apply --check "$p" || { echo "FAILED: $p"; exit 1; }
  git -C decomp apply "$p"
done

echo "== applying musyx patches =="
for p in "$ROOT"/patches/musyx/*.patch; do
  [ -e "$p" ] || continue
  echo "-> $p"
  git -C decomp/extern/musyx apply --check "$p" || { echo "FAILED: $p"; exit 1; }
  git -C decomp/extern/musyx apply "$p"
done

echo "== applying aurora patches =="
for p in "$ROOT"/patches/aurora/*.patch; do
  [ -e "$p" ] || continue
  echo "-> $p"
  git -C aurora apply --check "$p" || { echo "FAILED: $p"; exit 1; }
  git -C aurora apply "$p"
done

echo "== applying temporary decomp patches =="
for p in "$ROOT"/patches/tmp/*.patch; do
  [ -e "$p" ] || continue
  echo "-> $p"
  git -C decomp apply --check "$p" || { echo "FAILED: $p"; exit 1; }
  git -C decomp apply "$p"
done

echo "all patches applied successfully"
