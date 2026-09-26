# Runs

| date | machine | variants | change | headline |
|---|---|---|---|---|
| 2026-09-25 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | baseline, nocopy | first run on WikiText-103, context of 2048 tokens | nocopy drafts 4.48x faster than baseline without a static cache and 24.45x faster with the 541 MB cache. Load time is unchanged. |
| 2026-09-25 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | baseline, nocopy | context of 4096 tokens, the setting of the pull request that added the static cache | nocopy drafts 4.52x faster than baseline without a static cache and 25.58x faster with the 541 MB cache. Load time is unchanged. |

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
