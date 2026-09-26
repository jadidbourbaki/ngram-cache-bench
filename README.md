# ngram-cache-bench

We benchmark the n-gram caches that llama.cpp uses for lookup decoding.
Each variant in `variants.tsv` is a commit on
[our llama.cpp fork](https://github.com/jadidbourbaki/llama.cpp) and
changes one thing from the variant before it.

| variant | change |
|---|---|
| `baseline` | upstream llama.cpp at `84e76d8` |
| `nocopy` | the drafting loop reads cache entries by reference instead of copying them |
| `outermap` | every cache is an `unordered_dense` segmented map from each n-gram to a `std::unordered_map` of its following tokens |
| `innervector` | the following tokens of each n-gram are a vector of (token, count) pairs sorted by token |
| `constmap` | the static cache is a verified constmap from each 2-gram to a span of (token, count) pairs sorted by token |
We build static caches from [WikiText-103](https://arxiv.org/abs/1609.07843)
(2016) train and replay WikiText-103 test through `llama-lookup-stats`.
The tokenizer is Qwen2.5 0.5B Instruct. Our results are in
[results/tables.md](results/tables.md).

## Running

The benchmark runs on macOS and Linux with git, CMake, a C++17 compiler,
[uv](https://docs.astral.sh/uv/), and [just](https://github.com/casey/just).

```bash
git clone --recurse-submodules https://github.com/jadidbourbaki/ngram-cache-bench
cd ngram-cache-bench
just fetch corpora build stats followers plot
```

| step | what it does |
|---|---|
| `fetch` | downloads WikiText-103 and the tokenizer model at pinned Hugging Face revisions |
| `corpora` | cuts WikiText-103 train into nested corpora of 25, 50, 100, 200, and 541 MB |
| `build` | checks out and builds every variant under `work/` |
| `stats` | builds the missing static caches and runs `llama-lookup-stats` 3 times per variant and corpus |
| `followers` | counts the distinct tokens that follow each 2-gram of the 541 MB static cache into `results/followers.csv` |
| `plot` | writes `results/tables.md`, the figures comparing every variant with the variant before it in `results/figures/<variant>/`, and the distribution of followers in `results/figures/followers.svg` |

`stats --variants NAME ...` measures only the named variants and keeps
the recorded runs of the others, so a new variant does not rerun the old
ones.

`llama-lookup-stats` runs with these settings.

| flag | value | meaning |
|---|---|---|
| `-c` | 4096 | tokens replayed as one generation |
| `--spec-draft-n-max` | 8 | most tokens drafted per step |
| `-ngl` | 0 | run on the CPU |

The tables report the median of the 3 runs. The figures draw the median
as a bar and the fastest to the slowest run as an error bar. The corpora
are prefixes of the train text, so each corpus contains every smaller one.
The memory figures show the peak resident memory of each run, which holds
the model, the context and dynamic caches, and the static cache. The
tables also report the memory of a static cache alone, which is the peak
of a run with the cache minus the peak of the same variant without one.
Every run is in `results/lookup_stats.csv` and
every static cache is in `results/lookup_create.csv`.
