# Runs

| date | machine | variants | change | headline |
|---|---|---|---|---|
| 2026-09-25 | Apple M4 Pro, 14 cores, 48 GiB, macOS 26.5.1 | baseline, nocopy | first run on WikiText-103 | nocopy drafts 4.48x faster than baseline without a static cache and 24.45x faster with the 541 MB cache. Load time is unchanged. |

In the first run, nocopy drafts about 0.2% fewer tokens than baseline and
accepts up to 0.16 percentage points more of them. The drafting loop keeps
the first continuation with the highest count, and copying a libc++
`std::unordered_map` changes the order in which its entries iterate, so
baseline and nocopy break ties between equally frequent continuations
differently. Every configuration drafted the same number of tokens in all
3 runs. One baseline run with the 50 MB cache drafted at 107 µs per
drafted token against a median of 63 µs. nocopy also peaks 35 to 74 MB higher than baseline with a static
cache, and we have not found the cause.
