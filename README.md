# ngram-cache-bench

We benchmark the n-gram caches that llama.cpp uses for lookup decoding.
Each variant in `variants.tsv` is a commit on
[our llama.cpp fork](https://github.com/jadidbourbaki/llama.cpp) and
changes one thing from the variant before it.

| variant | change |
|---|---|
| `baseline` | upstream llama.cpp at `84e76d8` |
| `nocopy` | the drafting loop reads cache entries by reference instead of copying them |
| `flatmap` | every cache is a flat `unordered_dense` map from n-gram to a vector of following tokens sorted by token |

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
just fetch corpora build stats plot
```

| step | what it does |
|---|---|
| `fetch` | downloads WikiText-103 and the tokenizer model at pinned Hugging Face revisions |
| `corpora` | cuts WikiText-103 train into nested corpora of 25, 50, 100, 200, and 541 MB |
| `build` | checks out and builds every variant under `work/` |
| `stats` | builds the missing static caches and runs `llama-lookup-stats` 3 times per variant and corpus |
| `plot` | writes `results/tables.md` and, for every variant, figures comparing it with the variant before it in `results/figures/<variant>/` |

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
The memory of a static cache
is the peak resident memory of a run with the cache minus the peak of the
same variant without one. Every run is in `results/lookup_stats.csv` and
every static cache is in `results/lookup_create.csv`.
