"""Check out every llama.cpp variant as a worktree of the submodule and build its lookup tools."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ngram_cache_bench.paths import SUBMODULE_DIR, WORK_DIR
from ngram_cache_bench.variants import load_variants

TOOLS = ["llama-lookup-create", "llama-lookup-stats"]


def source_dir(variant_name: str) -> Path:
    return WORK_DIR / "src" / variant_name


def build_dir(variant_name: str) -> Path:
    return WORK_DIR / "build" / variant_name


def tool_path(variant_name: str, tool: str) -> Path:
    return build_dir(variant_name) / "bin" / tool


def run() -> None:
    for variant in load_variants():
        variant_source = source_dir(variant.name)
        variant_build = build_dir(variant.name)
        if not variant_source.exists():
            subprocess.run(
                ["git", "-C", str(SUBMODULE_DIR), "fetch", "--depth", "1", "origin", variant.commit],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(SUBMODULE_DIR),
                    "worktree",
                    "add",
                    "--detach",
                    str(variant_source),
                    variant.commit,
                ],
                check=True,
            )
        configure = [
            "cmake",
            "-S",
            str(variant_source),
            "-B",
            str(variant_build),
            "-DCMAKE_BUILD_TYPE=Release",
            "-DLLAMA_BUILD_TESTS=OFF",
            "-DLLAMA_BUILD_SERVER=OFF",
        ]
        subprocess.run(configure, check=True)
        subprocess.run(["cmake", "--build", str(variant_build), "-j", "--target", *TOOLS], check=True)
        print(f"built {variant.name} at {variant.commit}", flush=True)
