"""Count how many distinct tokens follow each 2-gram of the largest legacy static cache."""

from __future__ import annotations

import collections
import struct

from ngram_cache_bench.results import FOLLOWERS_PATH, FollowersRow, write_rows
from ngram_cache_bench.stats import cache_path

# A legacy cache file is a sequence of records. A record holds the n-gram as 4 tokens of 4 bytes, the number of
# following tokens as 4 bytes, and then a 4-byte token and a 4-byte count for every following token. A 2-gram
# followed by 3 tokens takes 16 + 4 + 3 * 8 = 44 bytes.
NGRAM_BYTES = 16
FOLLOWER_COUNT_BYTES = 4
FOLLOWER_BYTES = 8
FOLLOWER_COUNT_FORMAT = "<i"


def run() -> None:
    """Write the number of 2-grams with each number of distinct following tokens to results/followers.csv."""
    cache = cache_path("legacy", "full")
    if not cache.exists():
        raise SystemExit(f"{cache} is missing, run the stats step first")
    cache_bytes = cache.read_bytes()
    ngrams_by_followers = collections.Counter()
    offset = 0
    while offset < len(cache_bytes):
        follower_count_offset = offset + NGRAM_BYTES
        unpacked = struct.unpack_from(FOLLOWER_COUNT_FORMAT, cache_bytes, follower_count_offset)
        followers = unpacked[0]
        ngrams_by_followers[followers] += 1
        offset = follower_count_offset + FOLLOWER_COUNT_BYTES + followers * FOLLOWER_BYTES
    if offset != len(cache_bytes):
        raise SystemExit(f"{cache} ends inside a record at byte {len(cache_bytes)}")
    rows = [
        FollowersRow(followers=followers, ngrams=ngrams)
        for followers, ngrams in sorted(ngrams_by_followers.items())
    ]
    write_rows(FOLLOWERS_PATH, rows)
    total_ngrams = sum(ngrams_by_followers.values())
    print(f"counted the followers of {total_ngrams} 2-grams in {cache.name}", flush=True)
