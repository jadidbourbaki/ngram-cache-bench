# Download WikiText-103 and the tokenizer model
fetch:
    uv run scripts/fetch_data.py

# Cut WikiText-103 train into the corpora that the static caches are built from
corpora:
    uv run scripts/make_corpora.py

# Check out and build every llama.cpp variant in variants.tsv
build:
    ./scripts/build_variants.sh

# Build every static cache and run llama-lookup-stats with every variant
stats:
    ./scripts/run_lookup_stats.sh

# Format the Python scripts
fmt:
    uv run ruff format scripts

# Lint and type check the scripts, the way the quality gate runs them
check:
    uv run ruff format --check scripts
    uv run ruff check scripts
    uv run ty check scripts
    shellcheck scripts/*.sh
