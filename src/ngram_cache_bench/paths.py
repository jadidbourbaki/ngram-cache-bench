"""Locations of the repo's inputs, working files, and results."""

from __future__ import annotations

from pathlib import Path

# The package lives at src/ngram_cache_bench, two levels below the repo root.
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
WORK_DIR = ROOT / "work"
RESULTS_DIR = ROOT / "results"
SUBMODULE_DIR = ROOT / "llama.cpp"
VARIANTS_PATH = ROOT / "variants.tsv"
DOWNLOAD_DIR = DATA_DIR / "downloads"
MODEL_PATH = DOWNLOAD_DIR / "qwen2.5-0.5b-instruct-q4_k_m.gguf"
TRAIN_PATH = DATA_DIR / "wiki.train.raw"
HELD_OUT_PATH = DATA_DIR / "wiki.test.raw"
