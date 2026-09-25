# AGENTS.md

Guidance for AI agents working on ngram-cache-bench. The CLAUDE.md
symlink resolves to this file. Read it in full at the start of a
session.

## Project context

ngram-cache-bench measures the n-gram caches that llama.cpp uses for
lookup decoding. The repo pins every input a result depends on: the
llama.cpp variants, the corpus, and the tokenizer model. Anyone who
clones the repo and runs the steps in order gets the same numbers on
the same hardware.

The llama.cpp variants live on the fork at
[jadidbourbaki/llama.cpp](https://github.com/jadidbourbaki/llama.cpp),
which is the `llama.cpp` submodule. `variants.tsv` names each variant
and pins it to a commit on the fork. Each variant changes one thing
relative to the variant before it.

The corpus is [WikiText-103](https://arxiv.org/abs/1609.07843) (2016).
Static caches come from the train split and every measurement replays
the test split.

## Repository layout

```
variants.tsv        llama.cpp variants: name, fork commit, cache file format
llama.cpp/          submodule of the fork, checked out at the upstream base commit
src/ngram_cache_bench/  the ngram-cache-bench command, one module per step
results/            CSV results, tables, and figures that the steps write, committed
docs/runs.md        one row per benchmark run
data/               downloads and derived corpora, ignored by git
work/               per-variant worktrees, builds, caches, and logs, ignored by git
```

## Don't reinvent the wheel

Before writing any non-trivial logic, look for something already built.
Search the standard library first, then the dependencies already in
`pyproject.toml`, then PyPI. A mature package is almost always more
correct and better tested than a version written under deadline, and
every line not written is a line nobody has to review, test, or maintain.

Judge a candidate dependency by its maintenance and adoption: recent
releases, responsive maintainers, wide use in serious projects, a focused
scope. A good dependency is welcome. Reinvent only when nothing fits or
the dependency would weigh far more than the problem it solves.

In this repo that means: `llama-lookup-create` to build every static
cache and `llama-lookup-stats` for every measurement of drafting, each
from the variant under test, `huggingface_hub` for every download, and
polars for every aggregation and table. Before writing code for a new direction,
search for prior papers, existing benchmarks, and library support, and
present the choice with sources.

## Quality gate

`just check` runs `ruff format --check`, `ruff check`, and `ty check` on
`src/`. Work is complete when `just check` passes locally.

## Reproducibility

Every result in `results/` must be reproducible from a fresh clone.

- Pin every input. A llama.cpp variant is a full commit SHA in
  `variants.tsv`. A download is a commit of its Hugging Face repo, which
  fixes the bytes of every file. A Python dependency is an exact version
  in `pyproject.toml` with `uv.lock` committed.
- Read inputs only from the repo, `data/`, and `work/`. A path into a
  home directory, a Hugging Face cache, or a sibling checkout produces a
  result nobody else can reproduce.
- Scripts take no environment variables that change what they measure.
  A setting that changes a result is a constant in its module or a
  column in `variants.tsv`.
- Files under `results/` come from the steps. To change a number,
  change the step and rerun it.
- Push a variant's commit to the fork before pinning it. The build
  step fetches each variant by SHA, so an unpushed commit fails on
  every clone but the one it was made in.

## Experiment hygiene

- Every run writes its CSV files under `results/` with the variant
  commits, the corpus sizes, and the machine. The files are committed.
  Corpora, caches, and logs stay out of git.
- Log every run in `docs/runs.md` with one row: date, repo commit,
  machine, what changed, and the headline numbers.
- Run each timed configuration several times and report a fixed
  statistic. `llama-lookup-stats` runs report the median of 3 runs. Name
  the statistic next to every number a step prints.
- Check correctness in the same run as speed. The acceptance rate of
  `llama-lookup-stats` must match across variants that share drafting
  logic. A variant that changes how ties between equally frequent tokens
  break may differ by a few hundredths of a percentage point, and the run
  log says so.
- Log negative results with the same detail as positive ones.
- A change to the corpus, the tokenizer, or the method invalidates
  earlier results. Say so in `docs/runs.md` and rerun.
- Seed everything with 42.

## Writing prose

The following rules apply to all prose in the repo: README, docs, run
logs, commit messages, code comments, docstrings.

### Hard rules

- No em-dashes and no en-dashes. Split the sentence or use a comma.
- No semicolons in prose. Use a period and start a new sentence.
- No parenthetical asides. A parenthesis may hold an abbreviation on
  first use.
- No contrast constructions such as "X, not Y", "rather than Y", or
  "instead of Y". State what the code or the method does.
- No comma splices. Two independent clauses get two sentences.
- No ASCII diagrams. Describe relationships in prose.
- No emoji.
- No vague back-references. Do not open a sentence with "This",
  "That", "These", "Those", "Their", or "It" pointing at a noun from
  an earlier sentence. Name the noun again.
- No slogans, aphorisms, or stock metaphors. Every sentence names a
  concrete actor and a concrete object.
- No provenance credits. Do not write who added a feature or which PR
  introduced it. Cite only the sources an argument depends on.
- Put flags, constants, and their values in a table with a column for
  the name, the value, and the meaning.

### Soft rules

- Write short declarative sentences in the active voice. Docs use
  "we": "We build", "We then measure".
- Put the subject first.
- Define a term in the sentence where it first appears.
- Cite papers as markdown links with the title and year, for example
  [Binary Fuse Filters](https://arxiv.org/abs/2201.01174) (2022).

## Writing documentation

The README is read top to bottom by someone following along.

- Explain every code block. Never drop a command without saying what it
  does and what every meaningful flag means. Show output too, and say
  what its columns mean.
- Headings name content. A heading never narrates the act.
- Add a heading only where a genuinely new section begins.
- Cut words that earn nothing.

## Writing comments

- Docstrings are one line. Usage notes belong in the README.
- Where a line of code needs an explanation, a short comment sits above
  it. The comment says what the line does and why the code needs it
  here, in plain words, and gives numerical behavior as a numerical
  example: "a 2-gram key is 8 bytes, two 32-bit token IDs".
- Describe the present behavior and its reason. Do not describe the
  history of the code or pull requests.
- No comment repeats what a well-named identifier already says.
- No multi-line comment banners.

## Code readability

These rules apply to every language in the repo.

- One assignment per line. No tuple packing such as `a, b = 1, 2`.
- Descriptive names: `held_out_tokens`, `cache_bytes`, `draft_ms`. A
  single letter is acceptable only as a comprehension or loop index.
- Name intermediate results. Do not chain calls.
- Fail hard. No `try/except: pass`. No silent fallbacks. A missing
  input or a tool that exits nonzero stops the step
  with a message that names the offending value.
- Match the scope of a change to the request. A step does not need a
  helper module.

### Python

- uv for environments and dependencies: `uv add`, `uv lock`, `uv run`.
  ruff for linting and formatting. ty for type checking. just for task
  running.
- Runtime dependencies go in `[project].dependencies`. Dev tools go in
  `[dependency-groups].dev`. Pin every direct dependency to an exact
  version with `==` and commit `uv.lock`. The lockfile is never
  hand-edited.
- Put `from __future__ import annotations` at the top of every module.
- Type every function signature, parameters and return. Use built-in
  generics such as `list[int]` and `dict[str, T]`, and `X | None`.
- Validate inputs at the boundary with pydantic models and pass those
  models across function boundaries. A row read from `variants.tsv` or
  a results CSV is a pydantic model.
- Every import goes at the top of the module. An import inside a
  function needs a comment naming the circular import it avoids.
- `snake_case` for functions and variables, `PascalCase` for classes,
  `UPPER_SNAKE` for module constants. A leading underscore marks a name
  module-private.
- Signal failure by raising an exception. Catch narrowly. A bare
  `except:` is never correct. Use `raise ... from err` to preserve the
  cause.

- The repo is one package under `src/` built with `uv_build`. Every step
  is a module with a `run()` function and a subcommand of the
  `ngram-cache-bench` entry point in `[project.scripts]`.
- Call external programs such as git, CMake, and the llama.cpp tools
  with `subprocess` and `check=True`.

## Writing tests

A test earns its place by being able to fail for a real defect. Before
adding one, name the defect it would catch and the result that defect
would corrupt. Delete a test whose only failure mode is already covered
by a stronger test.

The results of this repo rest on a few properties, and each one fails
loudly when it breaks.

- Every download comes from its pinned Hugging Face revision.
- Each corpus is a prefix of the next one and ends at a line boundary.
- Variants that share drafting logic report the same acceptance rate on
  the same cache.

## Commit messages

Conventional commits, one sentence each, no body.

```
feat: add a variant with flat hash maps for every cache
fix: restore the blank lines of the WikiText parquet files
docs: log the first WikiText-103 run
chore: pin the nocopy variant to its rebased commit
```

- Lowercase the type and the first word after the colon, unless it is a
  proper noun or acronym.
- No `Co-Authored-By` trailer and no "Generated with" line.
- Do not amend or rewrite published commits without explicit user
  consent. Force-push only with `--force-with-lease`, only on a feature
  branch, and only after confirming.

## Git practices

- Use the git identity the user has configured. Never pass
  `-c user.email` or `-c user.name`.
- Ask before every commit and every push, each time, even after a prior
  yes. The same rule covers the fork: pushing a variant branch, opening
  a PR, and force-pushing a rebased branch each need their own approval.
- Confirm with the user before any destructive operation.

## Working with the user

- Local, reversible actions such as editing a file or running a
  benchmark need no preamble. Actions that are hard to reverse need
  explicit confirmation each time. Authorization for one action does
  not extend to similar actions.
- Lay out a plan before destructive multi-step work. Get a green light,
  then execute. After every destructive step, summarize the state.
- When you spot a side effect the user did not ask for, name it and ask
  before doing it.
- Default to terse. Lead with the result.
- End a turn with one or two sentences: what shipped and what is next.
- Do not restate the request.

## When in doubt

Re-read this document, then the most recent changes that touched the
same area. Match the existing patterns.
