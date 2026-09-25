"""Cut WikiText-103 train into nested corpora that each end at a line boundary."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
TRAIN_PATH = DATA_DIR / "wiki.train.raw"
CORPUS_SIZES_MB = [25, 50, 100, 200]
BYTES_PER_MB = 1_000_000


def write_prefix(train_bytes: bytes, limit: int, out_path: Path) -> None:
    last_newline = train_bytes.rindex(b"\n", 0, limit)
    prefix = train_bytes[: last_newline + 1]
    out_path.write_bytes(prefix)
    print(f"{out_path.relative_to(ROOT)}: {len(prefix)} bytes")


if not TRAIN_PATH.exists():
    raise SystemExit(f"{TRAIN_PATH} is missing, run scripts/fetch_data.py first")

train_bytes = TRAIN_PATH.read_bytes()
for size_mb in CORPUS_SIZES_MB:
    write_prefix(train_bytes, size_mb * BYTES_PER_MB, DATA_DIR / f"corpus-{size_mb}mb.txt")
write_prefix(train_bytes, len(train_bytes), DATA_DIR / "corpus-full.txt")
