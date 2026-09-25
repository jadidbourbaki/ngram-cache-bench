"""Download the raw WikiText-103 text and the Qwen2.5 0.5B tokenizer model at pinned revisions."""

from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

from ngram_cache_bench.paths import DOWNLOAD_DIR, HELD_OUT_PATH, MODEL_PATH, ROOT, TRAIN_PATH

# A revision is a commit of the Hugging Face repo, so it pins the exact bytes of every file.
WIKITEXT_REPO = "Salesforce/wikitext"
WIKITEXT_REVISION = "b08601e04326c79dfdd32d625aee71d232d685c3"
WIKITEXT_TRAIN_FILES = [
    "wikitext-103-raw-v1/train-00000-of-00002.parquet",
    "wikitext-103-raw-v1/train-00001-of-00002.parquet",
]
WIKITEXT_TEST_FILES = ["wikitext-103-raw-v1/test-00000-of-00001.parquet"]

MODEL_REPO = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
MODEL_REVISION = "9217f5db79a29953eb74d5343926648285ec7e67"


def download_wikitext(file_names: list[str]) -> list[Path]:
    paths = []
    for file_name in file_names:
        path = hf_hub_download(
            WIKITEXT_REPO,
            file_name,
            repo_type="dataset",
            revision=WIKITEXT_REVISION,
            local_dir=DOWNLOAD_DIR,
        )
        paths.append(Path(path))
    return paths


def write_raw_text(parquet_paths: list[Path], out_path: Path) -> None:
    # Each parquet row is one line of the original wiki.*.raw file, newline included. Hugging Face
    # stores the original " \n" blank lines as empty rows, so we restore them to get the original bytes.
    with open(out_path, "w", encoding="utf-8") as out:
        for parquet_path in parquet_paths:
            table = pq.read_table(parquet_path, columns=["text"])
            lines = table.column("text").to_pylist()
            restored_lines = [line if line else " \n" for line in lines]
            out.writelines(restored_lines)
    print(f"{out_path.relative_to(ROOT)}: {out_path.stat().st_size} bytes", flush=True)


def run() -> None:
    train_parquet_paths = download_wikitext(WIKITEXT_TRAIN_FILES)
    test_parquet_paths = download_wikitext(WIKITEXT_TEST_FILES)
    hf_hub_download(MODEL_REPO, MODEL_PATH.name, revision=MODEL_REVISION, local_dir=DOWNLOAD_DIR)
    write_raw_text(train_parquet_paths, TRAIN_PATH)
    write_raw_text(test_parquet_paths, HELD_OUT_PATH)
