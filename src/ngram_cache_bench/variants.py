"""The llama.cpp variants that variants.tsv pins to commits on the fork."""

from __future__ import annotations

import csv

from pydantic import BaseModel

from ngram_cache_bench.paths import VARIANTS_PATH


class Variant(BaseModel):
    name: str
    commit: str
    cache_format: str


def load_variants() -> list[Variant]:
    with open(VARIANTS_PATH, newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    return [Variant.model_validate(row) for row in rows]
