"""Cut WikiText-103 train into nested corpora that each end at a line boundary."""

from __future__ import annotations

from pathlib import Path

from ngram_cache_bench.paths import DATA_DIR, ROOT, TRAIN_PATH

CORPUS_SIZES_MB = [25, 50, 100, 200]
BYTES_PER_MB = 1_000_000
# Every corpus name in order of size. "full" is the whole 541 MB train text.
CORPUS_NAMES = [f"{size_mb}mb" for size_mb in CORPUS_SIZES_MB] + ["full"]
CORPUS_LABELS = {
    "25mb": "25 MB",
    "50mb": "50 MB",
    "100mb": "100 MB",
    "200mb": "200 MB",
    "full": "541 MB",
}


def corpus_path(corpus_name: str) -> Path:
    return DATA_DIR / f"corpus-{corpus_name}.txt"


def write_prefix(train_bytes: bytes, limit: int, out_path: Path) -> None:
    last_newline = train_bytes.rindex(b"\n", 0, limit)
    prefix = train_bytes[: last_newline + 1]
    out_path.write_bytes(prefix)
    print(f"{out_path.relative_to(ROOT)}: {len(prefix)} bytes", flush=True)


def run() -> None:
    if not TRAIN_PATH.exists():
        raise SystemExit(f"{TRAIN_PATH} is missing, run `ngram-cache-bench fetch` first")
    train_bytes = TRAIN_PATH.read_bytes()
    for size_mb in CORPUS_SIZES_MB:
        write_prefix(train_bytes, size_mb * BYTES_PER_MB, corpus_path(f"{size_mb}mb"))
    write_prefix(train_bytes, len(train_bytes), corpus_path("full"))
