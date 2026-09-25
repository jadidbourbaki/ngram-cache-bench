"""Draw the figures and write the markdown tables of results/ from the benchmark CSV files."""

from __future__ import annotations

from pathlib import Path

import polars as pl
from matplotlib.figure import Figure

from ngram_cache_bench.corpora import CORPUS_LABELS, CORPUS_NAMES
from ngram_cache_bench.paths import RESULTS_DIR, ROOT
from ngram_cache_bench.results import (
    CREATE_PATH,
    MACHINE_PATH,
    STATS_PATH,
    CreateRow,
    Machine,
    StatsRow,
    read_rows,
)
from ngram_cache_bench.variants import load_variants

FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_PATH = RESULTS_DIR / "tables.md"
BYTES_PER_MB = 1_000_000
LABELS = {"none": "none", **CORPUS_LABELS}
# Figures place corpora on an axis of megabytes, where 0 is a run without a static cache.
AXIS_LABELS = {"none": "0", "25mb": "25", "50mb": "50", "100mb": "100", "200mb": "200", "full": "541"}
X_AXIS_TITLE = "WikiText-103 training text in the static cache (MB)"
METRICS = ["draft_us_per_token", "load_ms", "accept_pct", "cache_memory_mb"]
# Colors follow the variant in the order of variants.tsv, from a palette checked for color vision deficiency.
SERIES_COLORS = ["#eb6834", "#2a78d6", "#1baf7a", "#eda100"]
SURFACE_COLOR = "#ffffff"
TEXT_COLOR = "#1a1a1a"
MUTED_COLOR = "#666666"
GRID_COLOR = "#e5e5e5"


def per_run_metrics(stats: pl.DataFrame) -> pl.DataFrame:
    """Return every metric of every run of llama-lookup-stats."""
    draft_us_per_token = 1000 * pl.col("draft_ms") / pl.col("n_drafted")
    # Memory of the static cache is the peak resident memory above the median run of the same variant without one.
    runs_without_cache = stats.filter(pl.col("corpus") == "none")
    peak_without_cache = pl.col("peak_rss_bytes").median().alias("peak_rss_without_cache")
    without_cache = runs_without_cache.group_by("variant").agg(peak_without_cache)
    joined = stats.join(without_cache, on="variant")
    cache_memory_mb = (pl.col("peak_rss_bytes") - pl.col("peak_rss_without_cache")) / BYTES_PER_MB
    return joined.with_columns(
        draft_us_per_token.alias("draft_us_per_token"),
        cache_memory_mb.alias("cache_memory_mb"),
    )


def aggregate(runs: pl.DataFrame, statistic: str) -> pl.DataFrame:
    """Return one statistic of every metric per variant and corpus, where statistic is median, min, or max."""
    metric_columns = pl.col(METRICS)
    expressions = {
        "median": metric_columns.median(),
        "min": metric_columns.min(),
        "max": metric_columns.max(),
    }
    return runs.group_by("variant", "corpus").agg(expressions[statistic])


def metric_table(
    summary: pl.DataFrame, metric: str, corpora: list[str], variant_names: list[str]
) -> pl.DataFrame:
    """Return one row per corpus and one column per variant, plus the ratio of each variant to the first."""
    wide = summary.pivot(on="variant", index="corpus", values=metric)
    corpus_order = pl.DataFrame({"corpus": corpora})
    ordered = corpus_order.join(wide, on="corpus", how="left")
    reference = variant_names[0]
    ratios = [(pl.col(reference) / pl.col(name)).alias(f"{reference} / {name}") for name in variant_names[1:]]
    labeled = ordered.with_columns(pl.col("corpus").replace_strict(LABELS))
    return labeled.select("corpus", *variant_names, *ratios)


def grouped_bars(
    path: Path,
    statistics: dict[str, pl.DataFrame],
    metric: str,
    corpora: list[str],
    variant_names: list[str],
    ylabel: str,
) -> None:
    """Draw the median of each variant as a bar and the fastest to slowest run as an error bar."""
    tables = {name: metric_table(table, metric, corpora, variant_names) for name, table in statistics.items()}
    figure = Figure(figsize=(7.2, 3.6), dpi=100, facecolor=SURFACE_COLOR)
    axes = figure.add_subplot()
    axes.set_facecolor(SURFACE_COLOR)
    bar_width = 0.8 / len(variant_names)
    tallest = max(tables["max"].select(variant_names).max().row(0))
    for index, name in enumerate(variant_names):
        medians = tables["median"][name].to_list()
        minimums = tables["min"][name].to_list()
        maximums = tables["max"][name].to_list()
        below = [median - minimum for median, minimum in zip(medians, minimums, strict=True)]
        above = [maximum - median for median, maximum in zip(medians, maximums, strict=True)]
        offsets = [position - 0.4 + bar_width * (index + 0.5) for position in range(len(corpora))]
        axes.bar(
            offsets,
            medians,
            bar_width,
            yerr=[below, above],
            error_kw={"ecolor": TEXT_COLOR, "elinewidth": 1, "capsize": 3},
            label=name,
            color=SERIES_COLORS[index],
            edgecolor=SURFACE_COLOR,
            linewidth=2,
            zorder=3,
        )
    axes.set_xticks(list(range(len(corpora))))
    axes.set_xticklabels([AXIS_LABELS[corpus] for corpus in corpora])
    axes.set_xlabel(X_AXIS_TITLE, color=TEXT_COLOR)
    axes.set_ylabel(ylabel, color=TEXT_COLOR)
    axes.set_ylim(0, tallest * 1.1)
    axes.grid(axis="y", color=GRID_COLOR, linewidth=1, zorder=0)
    axes.spines[["top", "right"]].set_visible(False)
    axes.tick_params(length=0, colors=MUTED_COLOR)
    axes.legend(frameon=False, loc="upper left")
    figure.tight_layout()
    figure.savefig(path, facecolor=SURFACE_COLOR)
    # GitHub renders PNG images in pull request descriptions, so every figure also gets a PNG copy.
    figure.savefig(path.with_suffix(".png"), facecolor=SURFACE_COLOR, dpi=200)


def markdown(title: str, table: pl.DataFrame, decimals: int) -> str:
    """Render a table as markdown with values at the given decimals and ratio columns as "4.48x"."""
    float_columns = [name for name, dtype in table.schema.items() if dtype == pl.Float64]
    ratio_columns = [name for name in float_columns if " / " in name]
    value_columns = [name for name in float_columns if name not in ratio_columns]
    formatted_values = [
        pl.col(name).map_elements(lambda value: f"{value:.{decimals}f}", return_dtype=pl.String)
        for name in value_columns
    ]
    formatted_ratios = [
        pl.col(name).map_elements(lambda value: f"{value:.2f}x", return_dtype=pl.String)
        for name in ratio_columns
    ]
    formatted = table.with_columns(*formatted_values, *formatted_ratios)
    with pl.Config(
        tbl_formatting="MARKDOWN",
        tbl_hide_column_data_types=True,
        tbl_hide_dataframe_shape=True,
        tbl_rows=-1,
        tbl_cols=-1,
        tbl_width_chars=1000,
        fmt_str_lengths=1000,
    ):
        rendered = str(formatted)
    return f"### {title}\n\n{rendered}\n"


def run() -> None:
    variant_names = [variant.name for variant in load_variants()]
    stats_rows = read_rows(STATS_PATH, StatsRow)
    create_rows = read_rows(CREATE_PATH, CreateRow)
    machine = read_rows(MACHINE_PATH, Machine)[0]
    stats = pl.DataFrame([row.model_dump() for row in stats_rows])
    runs = per_run_metrics(stats)
    statistics = {statistic: aggregate(runs, statistic) for statistic in ["median", "min", "max"]}
    medians = statistics["median"]
    all_corpora = ["none", *CORPUS_NAMES]

    drafting = metric_table(medians, "draft_us_per_token", all_corpora, variant_names)
    load = metric_table(medians, "load_ms", CORPUS_NAMES, variant_names)
    memory = metric_table(medians, "cache_memory_mb", CORPUS_NAMES, variant_names)
    acceptance = metric_table(medians, "accept_pct", all_corpora, variant_names)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    grouped_bars(
        FIGURES_DIR / "drafting.svg",
        statistics,
        "draft_us_per_token",
        all_corpora,
        variant_names,
        "drafting time per drafted token (µs)",
    )
    grouped_bars(
        FIGURES_DIR / "load.svg",
        statistics,
        "load_ms",
        CORPUS_NAMES,
        variant_names,
        "static cache load time (ms)",
    )
    grouped_bars(
        FIGURES_DIR / "memory.svg",
        statistics,
        "cache_memory_mb",
        CORPUS_NAMES,
        variant_names,
        "static cache memory (MB)",
    )

    caches = pl.DataFrame([row.model_dump() for row in create_rows])
    cache_files = caches.select(
        "cache_format",
        pl.col("corpus").replace_strict(LABELS),
        (pl.col("cache_bytes") / BYTES_PER_MB).alias("file (MB)"),
        (pl.col("peak_rss_bytes") / BYTES_PER_MB).alias("peak memory of llama-lookup-create (MB)"),
    )
    memory_gib = machine.memory_bytes / 2**30
    machine_line = f"{machine.cpu}, {machine.cores} cores, {memory_gib:.0f} GiB, {machine.os}"
    sections = [
        f"Machine: {machine_line}. Every value is the median of 3 runs of `llama-lookup-stats`.\n",
        markdown("Drafting time per drafted token (µs)", drafting, 2),
        markdown("Static cache load time (ms)", load, 0),
        markdown("Static cache memory (MB)", memory, 0),
        markdown("Accepted drafted tokens (%)", acceptance, 3),
        markdown("Static cache files", cache_files, 0),
    ]
    TABLES_PATH.write_text("\n".join(sections))
    print(f"wrote {TABLES_PATH.relative_to(ROOT)} and {FIGURES_DIR.relative_to(ROOT)}/", flush=True)
