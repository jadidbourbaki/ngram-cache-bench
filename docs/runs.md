# Runs

| date | machine | variants | change | headline |
|---|---|---|---|---|
| 2026-09-25 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | baseline, nocopy | first run on WikiText-103, context of 2048 tokens | nocopy drafts 4.48x faster than baseline without a static cache and 24.45x faster with the 541 MB cache. Load time is unchanged. |
| 2026-09-25 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | baseline, nocopy | context of 4096 tokens, the setting of the pull request that added the static cache | nocopy drafts 4.52x faster than baseline without a static cache and 25.58x faster with the 541 MB cache. Load time is unchanged. |
| 2026-09-25 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | flatmap | flat `unordered_dense` maps with a sorted vector of following tokens, measured alone with the recorded baseline and nocopy runs | flatmap drafts 2.56x faster than nocopy without a static cache and 0.98x to 1.12x as fast with one. flatmap loads the static cache 1.18x to 1.97x faster and holds it in 1.98x to 2.45x less memory. |
| 2026-09-26 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | outermap | outermap replaces flatmap and changes only the outer map | outermap drafts 1.04x to 1.16x faster than nocopy and loads the static cache 1.41x to 1.68x faster. outermap holds the 541 MB cache in 1.16x more memory. |
| 2026-09-26 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | constmap | a verified constmap backs the static cache, with a new static cache file format | constmap loads the static cache 9.81x to 14.87x faster than outermap and holds it in 5.15x to 6.76x less memory. constmap drafts 0.84x to 0.87x as fast with a static cache and at the same speed without one. |
| 2026-09-26 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | outermap, constmap | outermap stores the ngram caches in an `unordered_dense` segmented map, and constmap is rebased onto the new outermap | outermap loads the static cache 1.41x to 1.65x faster than nocopy, holds it in 1.07x to 1.11x less memory, and drafts 1.02x to 1.13x faster. constmap loads the static cache 8.18x to 15.07x faster than outermap, holds it in 4.31x to 5.29x less memory, and drafts 0.81x to 0.87x as fast with a static cache. |
| 2026-09-26 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | innervector, constmap | innervector stores the following tokens of each n-gram in a sorted vector on top of outermap, and constmap is rebased onto innervector | innervector drafts 2.26x faster than outermap without a static cache and 0.86x to 0.95x as fast with one, and holds the static cache in 2.42x to 2.87x less memory. constmap drafts 1.08x to 1.15x faster than innervector with a static cache, loads it 6.53x to 15.67x faster, and holds it in 1.87x to 2.20x less memory. |
| 2026-09-26 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | innervector, constmap | innervector searches the sorted followers without branches, constmap shares that search, and the memory figures show the whole peak | innervector drafts 2.09x faster than outermap without a static cache and 1.19x to 1.25x faster with one, and peaks 1.04x to 1.97x lower. constmap drafts 1.06x to 1.20x faster than innervector with a static cache, loads it 6.32x to 16.12x faster, and peaks up to 1.30x lower. |

The change of context size invalidates the first run, and `results/` holds
the second run.

In the first run, nocopy drafts 0.2% to 0.5% fewer tokens than baseline and
accepts up to 0.16 percentage points more of them. The drafting loop keeps
the first continuation with the highest count, and copying a libc++
`std::unordered_map` changes the order in which its entries iterate, so
baseline and nocopy break ties between equally frequent continuations
differently. Every configuration drafted the same number of tokens in all
3 runs. One baseline run with the 50 MB cache drafted at 107 µs per
drafted token against a median of 63 µs. nocopy also peaks 35 to 74 MB higher than baseline with a static
cache, and we have not found the cause.

The second run shows the same pattern. nocopy drafts 0.1% to 0.5% fewer tokens
and accepts up to 0.15 percentage points more of them, and every configuration
drafted the same number of tokens in all 3 runs. One baseline run with the
541 MB cache drafted at 310 µs per drafted token against a median of 165 µs.
nocopy peaks 34 to 79 MB higher than baseline with a static cache.

The third run measured flatmap in a later session than the baseline and
nocopy runs of the second run, on the same machine and with the same
static caches. flatmap iterates its sorted vectors in token order, so
flatmap breaks ties differently from nocopy. flatmap drafts 0.3% fewer
tokens than nocopy without a static cache and 0.08% to 0.14% more with one.
flatmap accepts up to 0.08 percentage points more of them. Every
configuration drafted the same number of tokens in all 3 runs.

The fourth run replaces flatmap with outermap, which keeps the
`std::unordered_map` of following tokens. The flatmap runs of the third
run stay in the history of `results/` at `c62c843`. outermap drafts and
accepts exactly the same number of tokens as nocopy on every cache,
because outermap keeps the order in which the following tokens iterate.

The fifth run builds new static caches with the `llama-lookup-create` of
constmap. The first attempt stopped when the second run of constmap
without a static cache exited with a bus error right after startup. Six
direct runs of the same command exited cleanly, and the rerun finished
every configuration. constmap stores the following tokens of each 2-gram
sorted by token, so constmap breaks ties differently from outermap and
accepts up to 0.06 percentage points more of the drafted tokens. Every
configuration drafted the same number of tokens in all 3 runs.

The sixth run replaces the fourth and fifth runs of outermap and constmap.
The `unordered_dense` map of the fourth run keeps its entries in one vector
that doubles as it fills. The 541 MB cache has 8,879,640 2-grams, so the
last doubling at 8,388,608 entries holds the old and the new vector at
once. The segmented map grows in blocks of 4096 bytes and removes that
peak. A single run with the 541 MB cache peaked at 3.35 GB with the
segmented map, 3.25 GB with an exact `reserve` from a first pass over the
file, and 4.01 GB with the plain map. The first pass added 0.4 s to the
load. We rebuilt the constmap static caches with the rebased
`llama-lookup-create`. Every configuration drafted the same number of
tokens in all 3 runs.

The seventh run adds innervector between outermap and constmap, so the
binary search over sorted followers now enters with innervector. We ran
innervector at `c512387` and constmap at `e96338d`, then pinned them to
`9bec231` and `948eb38`, which differ from the measured commits only by
the removal of a three-line comment in `common/ngram-cache.h`.
innervector breaks ties between equally frequent tokens in token order
and accepts up to 0.08 percentage points more drafted tokens than
outermap. We rebuilt the constmap static caches with the rebased
`llama-lookup-create`. Every configuration drafted the same number of
tokens in all 3 runs.

The eighth run replaces the seventh run of innervector and constmap. The
seventh run searched the sorted followers with `std::lower_bound`, which
made innervector draft 0.86x to 0.95x as fast as outermap with a static
cache. innervector now halves the search range a fixed number of times
for a given part length. Clang on the M4 Pro compiles the comparison of
both searches to a conditional select, so the searches differ in their
loop exit. The exit of `std::lower_bound` depends on the loaded tokens,
and the exit of the new search depends only on the part length. We have
not measured branch mispredictions. A linear scan of parts with at most 16 followers left
drafting unchanged in a quick test, because the slow searches are in the
parts of frequent 2-grams with thousands of followers. constmap stores
its spans as the same (token, count) pairs and calls the same search.
Without a static cache, constmap and innervector run the same code, and
their runs of 0.80 to 0.84 µs and 0.84 to 0.92 µs per drafted token
overlap. constmap drafts and accepts exactly the same tokens as
innervector on every corpus. We ran innervector at `e597b1b` and constmap
at `bdd4ea7`, then pinned them to `f46522c` and `b90b281`, which differ
from the measured commits only by the comment above the search in
`common/ngram-cache.h`.
