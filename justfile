# Download WikiText-103 and the tokenizer model at pinned revisions
fetch:
    uv run ngram-cache-bench fetch

# Cut WikiText-103 train into the corpora that the static caches are built from
corpora:
    uv run ngram-cache-bench corpora

# Check out and build every llama.cpp variant in variants.tsv
build:
    uv run ngram-cache-bench build

# Build every static cache and run llama-lookup-stats with every variant
stats:
    uv run ngram-cache-bench stats

# Count the distinct tokens that follow each 2-gram of the 541 MB static cache
followers:
    uv run ngram-cache-bench followers

# Draw the figures and write the tables of results/
plot:
    uv run ngram-cache-bench plot

# Format the code
fmt:
    uv run ruff format src

# Lint and type check the code, the way the quality gate runs them
check:
    uv run ruff format --check src
    uv run ruff check src
    uv run ty check src
