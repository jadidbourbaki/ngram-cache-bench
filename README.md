# ngram-cache-bench

We benchmark the n-gram caches that llama.cpp uses for lookup decoding.
Lookup decoding drafts tokens from counts of which token followed each
n-gram, and the model checks the drafted tokens in one batch. Each
llama.cpp variant in `variants.tsv` is a commit on the fork at
[jadidbourbaki/llama.cpp](https://github.com/jadidbourbaki/llama.cpp).
Each variant changes one thing relative to the variant before it.

| variant | change |
|---|---|
| `baseline` | upstream llama.cpp at `84e76d8` |
| `nocopy` | the drafting loop reads cache entries by reference instead of copying each inner map |

We build static caches from
[WikiText-103](https://arxiv.org/abs/1609.07843) (2016) train and replay
WikiText-103 test through `llama-lookup-stats`. The tokenizer is Qwen2.5
0.5B Instruct.

## Requirements

The scripts run on macOS and Linux. They need git, CMake, a C++17
compiler, [uv](https://docs.astral.sh/uv/), and
[just](https://github.com/casey/just). `just check` also needs
[shellcheck](https://www.shellcheck.net/).

## Running the benchmark

Clone the repo with its submodule:

```bash
git clone --recurse-submodules https://github.com/jadidbourbaki/ngram-cache-bench
cd ngram-cache-bench
```

The submodule is a shallow checkout of the fork. The build script fetches
each variant's commit by its SHA.

```bash
just fetch
```

`just fetch` downloads WikiText-103 and the tokenizer model from Hugging
Face at pinned revisions into `data/`. It checks every file against its
SHA-256 and stops on a mismatch. It then writes `data/wiki.train.raw` and
`data/wiki.test.raw`, which match the original WikiText-103 raw files
byte for byte.

```bash
just corpora
```

`just corpora` cuts the train text into corpora of 25, 50, 100, and
200 MB plus the full 541 MB. Each corpus is a prefix of the next one and
ends at a line boundary.

```bash
just build
```

`just build` checks out every variant as a worktree under `work/src/` and
builds `llama-lookup-create` and `llama-lookup-stats` under `work/build/`.

```bash
just stats
```

`just stats` builds one static cache per corpus with
`llama-lookup-create`. It then runs `llama-lookup-stats` 3 times for each
variant, once without a static cache and once with each corpus. The
settings are:

| setting | value | meaning |
|---|---|---|
| `-c` | 2048 | tokens per chunk that `llama-lookup-stats` replays as one generation |
| `--spec-draft-n-max` | 8 | most tokens drafted per step |
| `-ngl` | 0 | run on the CPU |

## Results

`just stats` writes two files under `results/`.

`results/lookup_create.csv` has one row per static cache.

| column | meaning |
|---|---|
| `cache_format` | file format of the static cache |
| `corpus` | corpus the cache was built from |
| `cache_bytes` | size of the cache file |
| `peak_rss_bytes` | peak resident memory of `llama-lookup-create` |

`results/lookup_stats.csv` has one row per run of `llama-lookup-stats`.

| column | meaning |
|---|---|
| `variant` | llama.cpp variant from `variants.tsv` |
| `corpus` | corpus of the static cache, or `none` |
| `run` | run number, from 1 to 3 |
| `load_ms` | time to load the static and dynamic caches |
| `draft_ms` | total time spent drafting and updating the context cache |
| `n_drafted` | number of drafted tokens |
| `n_accept` | number of drafted tokens that match the held-out text |
| `accept_pct` | `n_accept` as a percentage of `n_drafted` |
| `peak_rss_bytes` | peak resident memory of `llama-lookup-stats` |
