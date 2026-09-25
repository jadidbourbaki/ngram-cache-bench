"""Download the raw WikiText-103 text and the Qwen2.5 0.5B tokenizer model at pinned revisions."""

from __future__ import annotations

import hashlib
import shutil
import urllib.request
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DOWNLOAD_DIR = DATA_DIR / "downloads"

WIKITEXT_REVISION = "b08601e04326c79dfdd32d625aee71d232d685c3"
WIKITEXT_URL = (
    f"https://huggingface.co/datasets/Salesforce/wikitext/resolve/{WIKITEXT_REVISION}/wikitext-103-raw-v1"
)
WIKITEXT_FILES = {
    "train-00000-of-00002.parquet": "74da360f23826045b3e6ac6375411fdb15f003030aa74f2596ed08b857cb9212",
    "train-00001-of-00002.parquet": "ba090ac30dbf5461e8dcbdd1a1b8e6f3cf9c2c756d64f0c1220450acd514f720",
    "test-00000-of-00001.parquet": "5f1bea067869d04849c0f975a2b29c4ff47d867f484f5010ea5e861eab246d91",
}

MODEL_REVISION = "9217f5db79a29953eb74d5343926648285ec7e67"
MODEL_FILE = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
MODEL_URL = f"https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/{MODEL_REVISION}/{MODEL_FILE}"
MODEL_SHA256 = "74a4da8c9fdbcd15bd1f6d01d621410d31c6fc00986f5eb687824e7b93d7a9db"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, path: Path, expected_sha256: str) -> None:
    if not path.exists():
        print(f"downloading {url}")
        partial_path = path.with_suffix(path.suffix + ".partial")
        with urllib.request.urlopen(url) as response, open(partial_path, "wb") as out:
            shutil.copyfileobj(response, out)
        partial_path.rename(path)
    actual_sha256 = sha256_of(path)
    if actual_sha256 != expected_sha256:
        raise SystemExit(f"{path}: sha256 {actual_sha256} does not match {expected_sha256}")


def write_raw_text(parquet_paths: list[Path], out_path: Path) -> None:
    # Each parquet row is one line of the original wiki.*.raw file, newline included. Hugging Face
    # stores the original " \n" blank lines as empty rows, so we restore them to get the original bytes.
    with open(out_path, "w", encoding="utf-8") as out:
        for parquet_path in parquet_paths:
            table = pq.read_table(parquet_path, columns=["text"])
            lines = table.column("text").to_pylist()
            restored_lines = [line if line else " \n" for line in lines]
            out.writelines(restored_lines)
    print(f"{out_path.relative_to(ROOT)}: {out_path.stat().st_size} bytes")


DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
for file_name, expected_sha256 in WIKITEXT_FILES.items():
    download(f"{WIKITEXT_URL}/{file_name}", DOWNLOAD_DIR / file_name, expected_sha256)
download(MODEL_URL, DATA_DIR / "model.gguf", MODEL_SHA256)

write_raw_text(
    [DOWNLOAD_DIR / "train-00000-of-00002.parquet", DOWNLOAD_DIR / "train-00001-of-00002.parquet"],
    DATA_DIR / "wiki.train.raw",
)
write_raw_text([DOWNLOAD_DIR / "test-00000-of-00001.parquet"], DATA_DIR / "wiki.test.raw")
