"""Build a static cache from every corpus and run llama-lookup-stats with every selected variant."""

from __future__ import annotations

import os
import platform
import re
import subprocess
from pathlib import Path

from ngram_cache_bench import machine
from ngram_cache_bench.build import tool_path
from ngram_cache_bench.corpora import CORPUS_NAMES, corpus_path
from ngram_cache_bench.paths import HELD_OUT_PATH, MODEL_PATH, WORK_DIR
from ngram_cache_bench.results import CREATE_PATH, STATS_PATH, CreateRow, StatsRow, read_rows, write_rows
from ngram_cache_bench.variants import Variant, load_variants

CACHE_DIR = WORK_DIR / "caches"
LOG_DIR = WORK_DIR / "logs"
REPEATS = 3
# The pull request that added the static cache evaluated llama-lookup-stats with a context of 4096 tokens.
CONTEXT_SIZE = 4096
DRAFT_MAX = 8


def run_measured(command: list[str], log_path: Path) -> int:
    """Run a command with its output in a log file and return its peak resident memory in bytes."""
    with open(log_path, "w") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        # os.wait4 returns the process id, the wait status, and the resource usage of the child.
        wait_result = os.wait4(process.pid, 0)
    wait_status = wait_result[1]
    usage = wait_result[2]
    exit_code = os.waitstatus_to_exitcode(wait_status)
    process.returncode = exit_code
    if exit_code != 0:
        raise SystemExit(f"{command[0]} exited with {exit_code}, see {log_path}")
    # ru_maxrss counts bytes on macOS and kilobytes on Linux.
    if platform.system() == "Darwin":
        return usage.ru_maxrss
    return usage.ru_maxrss * 1024


def stat_value(log_text: str, name: str) -> str:
    # llama-lookup-stats prints lines such as "t_draft      = 1589.50 ms, 1.06 us per token".
    match = re.search(rf"\b{name}\s*=\s*([0-9.]+)", log_text)
    if match is None:
        raise SystemExit(f"llama-lookup-stats printed no {name}")
    return match.group(1)


def cache_path(cache_format: str, corpus_name: str) -> Path:
    return CACHE_DIR / f"static-{cache_format}-{corpus_name}.bin"


def select_variants(variant_names: list[str] | None) -> list[Variant]:
    """Return the variants of variants.tsv with the given names, or every variant when no names are given."""
    variants = load_variants()
    if variant_names is None:
        return variants
    known_names = {variant.name for variant in variants}
    unknown_names = [name for name in variant_names if name not in known_names]
    if unknown_names:
        raise SystemExit(f"variants.tsv has no variant named {', '.join(unknown_names)}")
    return [variant for variant in variants if variant.name in variant_names]


def create_caches(variants: list[Variant]) -> list[CreateRow]:
    """Build the missing static caches of the given variants and return a row for every cache on disk."""
    existing_rows = read_rows(CREATE_PATH, CreateRow) if CREATE_PATH.exists() else []
    rows_by_cache = {(row.cache_format, row.corpus): row for row in existing_rows}
    builders = {}
    for variant in variants:
        builders.setdefault(variant.cache_format, variant.name)
    for cache_format, builder in builders.items():
        for corpus_name in CORPUS_NAMES:
            cache = cache_path(cache_format, corpus_name)
            # A cache on disk with a recorded row came from the same pinned tool and corpus, so we reuse it.
            if cache.exists() and (cache_format, corpus_name) in rows_by_cache:
                print(f"reused {cache_format} cache for corpus {corpus_name}", flush=True)
                continue
            # llama-lookup-create writes to a partial file, so an interrupted run leaves no cache to reuse.
            partial_cache = cache.with_suffix(".partial")
            command = [
                str(tool_path(builder, "llama-lookup-create")),
                "-m",
                str(MODEL_PATH),
                "-f",
                str(corpus_path(corpus_name)),
                "-lcs",
                str(partial_cache),
                "-c",
                "512",
                "-ngl",
                "0",
            ]
            peak_rss_bytes = run_measured(command, LOG_DIR / f"create-{cache_format}-{corpus_name}.log")
            partial_cache.rename(cache)
            rows_by_cache[(cache_format, corpus_name)] = CreateRow(
                cache_format=cache_format,
                corpus=corpus_name,
                cache_bytes=cache.stat().st_size,
                peak_rss_bytes=peak_rss_bytes,
            )
            print(f"created {cache_format} cache for corpus {corpus_name}", flush=True)
    return list(rows_by_cache.values())


def run_stats(variants: list[Variant]) -> list[StatsRow]:
    rows = []
    for variant in variants:
        for corpus_name in ["none", *CORPUS_NAMES]:
            command = [
                str(tool_path(variant.name, "llama-lookup-stats")),
                "-m",
                str(MODEL_PATH),
                "-f",
                str(HELD_OUT_PATH),
                "-c",
                str(CONTEXT_SIZE),
                "--spec-draft-n-max",
                str(DRAFT_MAX),
                "-ngl",
                "0",
            ]
            if corpus_name != "none":
                command += ["-lcs", str(cache_path(variant.cache_format, corpus_name))]
            for run_number in range(1, REPEATS + 1):
                log_path = LOG_DIR / f"stats-{variant.name}-{corpus_name}-{run_number}.log"
                peak_rss_bytes = run_measured(command, log_path)
                log_text = log_path.read_text()
                rows.append(
                    StatsRow(
                        variant=variant.name,
                        corpus=corpus_name,
                        run=run_number,
                        load_ms=float(stat_value(log_text, "t_draft_flat")),
                        draft_ms=float(stat_value(log_text, "t_draft")),
                        n_drafted=int(stat_value(log_text, "n_drafted")),
                        n_accept=int(stat_value(log_text, "n_accept")),
                        accept_pct=float(stat_value(log_text, "accept")),
                        peak_rss_bytes=peak_rss_bytes,
                    )
                )
            print(f"ran {variant.name} with corpus {corpus_name}", flush=True)
    return rows


def run(variant_names: list[str] | None = None) -> None:
    """Measure the given variants, or every variant, and keep the recorded runs of the other variants."""
    variants = select_variants(variant_names)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    machine.run()
    create_rows = create_caches(variants)
    write_rows(CREATE_PATH, create_rows)
    measured_names = {variant.name for variant in variants}
    existing_rows = read_rows(STATS_PATH, StatsRow) if STATS_PATH.exists() else []
    kept_rows = [row for row in existing_rows if row.variant not in measured_names]
    new_rows = run_stats(variants)
    write_rows(STATS_PATH, kept_rows + new_rows)
