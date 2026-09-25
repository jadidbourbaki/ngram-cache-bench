#!/bin/sh
# Checks out every llama.cpp variant in variants.tsv as a worktree of the llama.cpp submodule
# and builds its lookup tools.
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)

tail -n +2 "$ROOT/variants.tsv" | while IFS="$(printf '\t')" read -r name commit cache_format; do
    src="$ROOT/work/src/$name"
    build="$ROOT/work/build/$name"
    if [ ! -d "$src" ]; then
        git -C "$ROOT/llama.cpp" fetch --depth 1 origin "$commit"
        git -C "$ROOT/llama.cpp" worktree add --detach "$src" "$commit"
    fi
    cmake -S "$src" -B "$build" -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_SERVER=OFF
    cmake --build "$build" -j --target llama-lookup-create llama-lookup-stats
    echo "built $name ($commit, $cache_format cache)"
done
