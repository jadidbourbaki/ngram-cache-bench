#!/bin/sh
# Builds a static n-gram cache from every corpus in each cache format, then runs
# llama-lookup-stats on the WikiText-103 test text with every variant in variants.tsv.
# Writes results/lookup_create.csv and results/lookup_stats.csv.
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
MODEL="$ROOT/data/model.gguf"
HELD_OUT="$ROOT/data/wiki.test.raw"
CACHE_DIR="$ROOT/work/caches"
LOG_DIR="$ROOT/work/logs"
RESULTS_DIR="$ROOT/results"
CORPORA="25mb 50mb 100mb 200mb full"
REPEATS=3
CONTEXT_SIZE=2048
DRAFT_MAX=8

mkdir -p "$CACHE_DIR" "$LOG_DIR" "$RESULTS_DIR"

# Runs a command with its output in a log file and appends the peak resident memory to the log.
run_measured() {
    log=$1
    shift
    case "$(uname)" in
        Darwin) /usr/bin/time -l "$@" > "$log" 2>&1 ;;
        Linux) /usr/bin/time -v "$@" > "$log" 2>&1 ;;
        *) echo "unsupported platform $(uname)" >&2; exit 1 ;;
    esac
}

peak_rss_bytes() {
    case "$(uname)" in
        Darwin) awk '/maximum resident set size/ { print $1 }' "$1" ;;
        Linux) awk -F': ' '/Maximum resident set size/ { print $2 * 1024 }' "$1" ;;
    esac
}

# Prints the number after "<name> =" in a llama-lookup-stats log.
stat_value() {
    sed -n "s/.* $2 *= *\([0-9.]*\).*/\1/p" "$1" | head -n 1
}

build_dir() {
    echo "$ROOT/work/build/$1/bin"
}

cache_path() {
    echo "$CACHE_DIR/static-$1-$2.bin"
}

variants=$(tail -n +2 "$ROOT/variants.tsv" | cut -f 1,3)

echo "cache_format,corpus,cache_bytes,peak_rss_bytes" > "$RESULTS_DIR/lookup_create.csv"
for format in $(echo "$variants" | cut -f 2 | sort -u); do
    builder=$(echo "$variants" | awk -v f="$format" '$2 == f { print $1; exit }')
    for corpus in $CORPORA; do
        cache=$(cache_path "$format" "$corpus")
        log="$LOG_DIR/create-$format-$corpus.log"
        run_measured "$log" "$(build_dir "$builder")/llama-lookup-create" \
            -m "$MODEL" -f "$ROOT/data/corpus-$corpus.txt" -lcs "$cache" -c 512 -ngl 0
        echo "$format,$corpus,$(wc -c < "$cache" | tr -d ' '),$(peak_rss_bytes "$log")" >> "$RESULTS_DIR/lookup_create.csv"
        echo "created $format cache for corpus $corpus"
    done
done

echo "variant,corpus,run,load_ms,draft_ms,n_drafted,n_accept,accept_pct,peak_rss_bytes" > "$RESULTS_DIR/lookup_stats.csv"
echo "$variants" | while IFS="$(printf '\t')" read -r variant format; do
    for corpus in none $CORPORA; do
        run=1
        while [ "$run" -le "$REPEATS" ]; do
            log="$LOG_DIR/stats-$variant-$corpus-$run.log"
            if [ "$corpus" = none ]; then
                run_measured "$log" "$(build_dir "$variant")/llama-lookup-stats" \
                    -m "$MODEL" -f "$HELD_OUT" -c "$CONTEXT_SIZE" --spec-draft-n-max "$DRAFT_MAX" -ngl 0
            else
                run_measured "$log" "$(build_dir "$variant")/llama-lookup-stats" \
                    -m "$MODEL" -f "$HELD_OUT" -lcs "$(cache_path "$format" "$corpus")" \
                    -c "$CONTEXT_SIZE" --spec-draft-n-max "$DRAFT_MAX" -ngl 0
            fi
            echo "$variant,$corpus,$run,$(stat_value "$log" t_draft_flat),$(stat_value "$log" t_draft),$(stat_value "$log" n_drafted),$(stat_value "$log" n_accept),$(stat_value "$log" accept),$(peak_rss_bytes "$log")" \
                >> "$RESULTS_DIR/lookup_stats.csv"
            run=$((run + 1))
        done
        echo "ran $variant with corpus $corpus"
    done
done
