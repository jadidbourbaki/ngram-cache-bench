"""Row models of the CSV files under results/, shared by the benchmark and the plots."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from ngram_cache_bench.paths import RESULTS_DIR

STATS_PATH = RESULTS_DIR / "lookup_stats.csv"
CREATE_PATH = RESULTS_DIR / "lookup_create.csv"
MACHINE_PATH = RESULTS_DIR / "machine.csv"
FOLLOWERS_PATH = RESULTS_DIR / "followers.csv"


class StatsRow(BaseModel):
    variant: str
    corpus: str
    run: int
    load_ms: float
    draft_ms: float
    n_drafted: int
    n_accept: int
    accept_pct: float
    peak_rss_bytes: int


class CreateRow(BaseModel):
    cache_format: str
    corpus: str
    cache_bytes: int
    peak_rss_bytes: int


class FollowersRow(BaseModel):
    followers: int
    ngrams: int


class Machine(BaseModel):
    cpu: str
    cores: int
    memory_bytes: int
    os: str


Row = TypeVar("Row", bound=BaseModel)


def write_rows(path: Path, rows: list[Row]) -> None:
    if not rows:
        raise SystemExit(f"no rows to write to {path}")
    field_names = list(type(rows[0]).model_fields)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=field_names)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.model_dump())


def read_rows(path: Path, model: type[Row]) -> list[Row]:
    if not path.exists():
        raise SystemExit(f"{path} is missing, run the benchmark first")
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    return [model.model_validate(row) for row in rows]
