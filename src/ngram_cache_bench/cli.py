"""The ngram-cache-bench command, with one subcommand per step of the benchmark."""

from __future__ import annotations

import argparse

from ngram_cache_bench import build, corpora, fetch, plot, stats

STEPS = {
    "fetch": ("download WikiText-103 and the tokenizer model at pinned revisions", fetch.run),
    "corpora": ("cut WikiText-103 train into the corpora of the static caches", corpora.run),
    "build": ("check out and build every llama.cpp variant in variants.tsv", build.run),
    "stats": ("build every static cache and run llama-lookup-stats with every variant", stats.run),
    "plot": ("draw the figures and write the tables of results/", plot.run),
}


def main() -> None:
    parser = argparse.ArgumentParser(prog="ngram-cache-bench", description=__doc__)
    subparsers = parser.add_subparsers(dest="step", required=True)
    for step, description_and_function in STEPS.items():
        help_text = description_and_function[0]
        subparsers.add_parser(step, help=help_text)
    arguments = parser.parse_args()
    step_function = STEPS[arguments.step][1]
    step_function()
