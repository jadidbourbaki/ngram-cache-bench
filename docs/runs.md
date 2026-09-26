# Runs

| date | machine | variants | change | headline |
|---|---|---|---|---|
| 2026-09-25 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | baseline, nocopy | first run on WikiText-103, context of 2048 tokens | nocopy drafts 4.48x faster than baseline without a static cache and 24.45x faster with the 541 MB cache. Load time is unchanged. |
| 2026-09-25 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | baseline, nocopy | context of 4096 tokens, the setting of the pull request that added the static cache | nocopy drafts 4.52x faster than baseline without a static cache and 25.58x faster with the 541 MB cache. Load time is unchanged. |
| 2026-09-25 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | flatmap | flat `unordered_dense` maps with a sorted vector of following tokens, measured alone with the recorded baseline and nocopy runs | flatmap drafts 2.56x faster than nocopy without a static cache and 0.98x to 1.12x as fast with one. flatmap loads the static cache 1.18x to 1.97x faster and holds it in 1.98x to 2.45x less memory. |

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
