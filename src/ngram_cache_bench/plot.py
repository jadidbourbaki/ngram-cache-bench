"""Draw the figures and write the markdown tables of results/ from the benchmark CSV files."""

from __future__ import annotations

import itertools
from pathlib import Path

import matplotlib
import polars as pl
from matplotlib.figure import Figure

from ngram_cache_bench.corpora import CORPUS_LABELS, CORPUS_NAMES
from ngram_cache_bench.paths import RESULTS_DIR, ROOT
from ngram_cache_bench.results import (
    CREATE_PATH,
    FOLLOWERS_PATH,
    MACHINE_PATH,
    STATS_PATH,
    CreateRow,
    FollowersRow,
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
# The size of the WikiText-103 training text each static cache was built from.
X_AXIS_TITLE = "Corpus Size (MB)"
METRICS = ["draft_us_per_token", "load_ms", "accept_pct", "cache_memory_mb", "peak_memory_mb"]

# A fixed salt gives the SVG elements the same ids on every run, so an unchanged figure has an unchanged file.
matplotlib.rcParams["svg.hashsalt"] = "42"
# Figures follow the look of a USENIX systems paper: the Times-like STIX serif that ships with matplotlib, a
# closed frame, and inward ticks. The numeric y axis repeats its ticks on the right, where a reader of the 541 MB
# bars reads their values. The categorical x axis has no ticks.
matplotlib.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["STIXGeneral"],
        "mathtext.fontset": "stix",
        # SVG figures keep their text as text, so a browser draws it with a hinted serif as sharp as the page text.
        "svg.fonttype": "none",
        "font.size": 11,
        "axes.labelsize": 11,
        "axes.linewidth": 1.0,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": False,
        "ytick.right": True,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "xtick.major.width": 1.0,
        "ytick.major.width": 1.0,
        "legend.fontsize": 10,
        "legend.handlelength": 1.2,
        "legend.borderpad": 0.4,
        "patch.linewidth": 0.8,
        "legend.frameon": True,
        "legend.fancybox": False,
        "legend.edgecolor": "black",
        "legend.framealpha": 1,
    }
)
# A figure 3 inches wide displays at 288 px in a browser without scaling, so three figures fit side by side in
# a blog column and 11 point text is 15 px.
FIGURE_SIZE_INCHES = (3.0, 2.4)
PNG_DPI = 300
# Bars follow the variant in the order of variants.tsv: an open black bar for the earlier variant and a filled
# black bar for the later one.
BAR_EDGE_COLOR = "#000000"
BAR_FACE_COLORS = ["#ffffff", "#000000"]
# The two bars of a corpus together fill 0.76 of the space between two corpus ticks.
BAR_WIDTH = 0.38
# Every error bar is ANSI red, so the ranges stand out against both open and filled bars.
ERROR_BAR_COLOR = "#ff0000"
SURFACE_COLOR = "#ffffff"
TEXT_COLOR = "#000000"
# A solid light grid stays sharp on a screen, where a thin dotted line breaks into uneven pixels.
GRID_COLOR = "#d9d9d9"


def per_run_metrics(stats: pl.DataFrame) -> pl.DataFrame:
    """Return every metric of every run of llama-lookup-stats."""
    draft_us_per_token = 1000 * pl.col("draft_ms") / pl.col("n_drafted")
    # Memory of the static cache is the peak resident memory above the median run of the same variant without one.
    runs_without_cache = stats.filter(pl.col("corpus") == "none")
    peak_without_cache = pl.col("peak_rss_bytes").median().alias("peak_rss_without_cache")
    runs_by_variant = runs_without_cache.group_by("variant")
    without_cache = runs_by_variant.agg(peak_without_cache)
    joined = stats.join(without_cache, on="variant")
    cache_memory_mb = (pl.col("peak_rss_bytes") - pl.col("peak_rss_without_cache")) / BYTES_PER_MB
    # Without a static cache, the peak holds the model and the context and dynamic caches. The model is the same
    # for every variant, so two variants differ in this peak by the memory of their context and dynamic caches.
    peak_memory_mb = pl.col("peak_rss_bytes") / BYTES_PER_MB
    return joined.with_columns(
        draft_us_per_token.alias("draft_us_per_token"),
        cache_memory_mb.alias("cache_memory_mb"),
        peak_memory_mb.alias("peak_memory_mb"),
    )


def aggregate(runs: pl.DataFrame, statistic: str) -> pl.DataFrame:
    """Return one statistic of every metric per variant and corpus, where statistic is median, min, or max."""
    metric_columns = pl.col(METRICS)
    expressions = {
        "median": metric_columns.median(),
        "min": metric_columns.min(),
        "max": metric_columns.max(),
    }
    runs_by_configuration = runs.group_by("variant", "corpus")
    return runs_by_configuration.agg(expressions[statistic])


def metric_table(
    summary: pl.DataFrame, metric: str, corpora: list[str], variant_names: list[str]
) -> pl.DataFrame:
    """Return one row per corpus and one column per variant, plus the ratio of each variant to the one before it."""
    wide = summary.pivot(on="variant", index="corpus", values=metric)
    corpus_order = pl.DataFrame({"corpus": corpora})
    ordered = corpus_order.join(wide, on="corpus", how="left")
    consecutive_pairs = itertools.pairwise(variant_names)
    ratios = [
        (pl.col(previous) / pl.col(name)).alias(f"{previous} / {name}")
        for previous, name in consecutive_pairs
    ]
    labeled = ordered.with_columns(pl.col("corpus").replace_strict(LABELS))
    return labeled.select("corpus", *variant_names, *ratios)


def grouped_bars(
    path: Path,
    statistics: dict[str, pl.DataFrame],
    metric: str,
    corpora: list[str],
    variant_names: list[str],
    ylabel: str,
    unit_divisor: float,
) -> None:
    """Draw the median of each variant as a bar and the fastest to slowest run as an error bar."""
    tables = {name: metric_table(table, metric, corpora, variant_names) for name, table in statistics.items()}
    figure = Figure(figsize=FIGURE_SIZE_INCHES, facecolor=SURFACE_COLOR)
    axes = figure.add_subplot()
    axes.set_facecolor(SURFACE_COLOR)
    positions = list(range(len(corpora)))
    for index, name in enumerate(variant_names):
        # The bars of a corpus sit side by side around its tick, so the first bar spans 0.38 left of the tick and
        # the second 0.38 right of it.
        offset = (index - 0.5) * BAR_WIDTH
        bar_positions = [position + offset for position in positions]
        # A unit divisor of 1000 draws 2652 MB as 2.652 GB.
        median_column = tables["median"][name] / unit_divisor
        minimum_column = tables["min"][name] / unit_divisor
        maximum_column = tables["max"][name] / unit_divisor
        medians = median_column.to_list()
        minimums = minimum_column.to_list()
        maximums = maximum_column.to_list()
        below = [median - minimum for median, minimum in zip(medians, minimums, strict=True)]
        above = [maximum - median for median, maximum in zip(medians, maximums, strict=True)]
        axes.bar(
            bar_positions,
            medians,
            BAR_WIDTH,
            color=BAR_FACE_COLORS[index],
            edgecolor=BAR_EDGE_COLOR,
            linewidth=1.0,
            label=name,
            zorder=2,
        )
        axes.errorbar(
            bar_positions,
            medians,
            yerr=[below, above],
            linestyle="none",
            ecolor=ERROR_BAR_COLOR,
            elinewidth=1.2,
            capsize=3,
            capthick=1.2,
            zorder=3,
        )
    axes.set_xticks(positions)
    axes.set_xticklabels([AXIS_LABELS[corpus] for corpus in corpora])
    axes.set_xlabel(X_AXIS_TITLE, color=TEXT_COLOR)
    axes.set_ylabel(ylabel, color=TEXT_COLOR)
    # Bars start at 0 on a linear axis, so a bar half as tall shows half the time or memory.
    axes.set_ylim(bottom=0)
    axes.grid(axis="y", which="major", color=GRID_COLOR, linestyle="-", linewidth=0.8, zorder=0)
    # The corpora are categories, and the bars already mark where each corpus sits.
    axes.tick_params(axis="x", which="both", bottom=False, top=False)
    # The bars grow with the corpus, so the upper left corner stays clear of the tallest bars on the right.
    axes.legend(loc="upper left")
    # matplotlib measures the text with STIX, but a browser draws the SVG text in its own serif, which can run a
    # few pixels past the STIX edges. A padding of 0.8 of the font size, 9 pt at 11 pt text, keeps that text inside
    # the figure.
    figure.tight_layout(pad=0.8)
    figure.savefig(path, facecolor=SURFACE_COLOR, metadata={"Date": None})
    # GitHub renders PNG images in pull request descriptions, so every figure also gets a PNG copy.
    png_path = path.with_suffix(".png")
    figure.savefig(png_path, facecolor=SURFACE_COLOR, dpi=PNG_DPI)


def followers_cdf(path: Path, followers_rows: list[FollowersRow]) -> None:
    """Draw the cumulative share of 2-grams and of (2-gram, token) pairs by the number of distinct followers."""
    followers = pl.DataFrame([row.model_dump() for row in followers_rows])
    # A 2-gram with 3 followers holds 3 (2-gram, token) pairs.
    pairs = pl.col("followers") * pl.col("ngrams")
    cumulative_ngrams = pl.col("ngrams").cum_sum() / pl.col("ngrams").sum()
    cumulative_pairs = pairs.cum_sum() / pairs.sum()
    sorted_followers = followers.sort("followers")
    shares = sorted_followers.with_columns(
        cumulative_ngrams.alias("ngram_share"),
        cumulative_pairs.alias("pair_share"),
    )
    follower_counts = shares["followers"].to_list()
    ngram_shares = shares["ngram_share"].to_list()
    pair_shares = shares["pair_share"].to_list()
    figure = Figure(figsize=FIGURE_SIZE_INCHES, facecolor=SURFACE_COLOR)
    axes = figure.add_subplot()
    axes.set_facecolor(SURFACE_COLOR)
    # The counts are whole numbers, so each line steps up at a count and stays flat until the next one.
    axes.step(
        follower_counts, ngram_shares, where="post", color=BAR_EDGE_COLOR, linewidth=1.2, label="2-grams"
    )
    axes.step(
        follower_counts,
        pair_shares,
        where="post",
        color=BAR_EDGE_COLOR,
        linewidth=1.2,
        linestyle="--",
        label="(2-gram, token) pairs",
    )
    # Counts run from 1 to more than 20,000 followers, so the axis is logarithmic and reads 10^0 to 10^4.
    axes.set_xscale("log")
    axes.set_xlim(1, follower_counts[-1])
    axes.set_ylim(0, 1)
    axes.set_xlabel("Distinct Followers of a 2-gram", color=TEXT_COLOR)
    axes.set_ylabel("Cumulative Share", color=TEXT_COLOR)
    axes.grid(axis="y", which="major", color=GRID_COLOR, linestyle="-", linewidth=0.8, zorder=0)
    # Both lines stay above 0.3 right of 10 followers, so the legend hugs the lower right corner below them.
    axes.legend(loc="lower right", borderaxespad=0.3)
    figure.tight_layout(pad=0.8)
    figure.savefig(path, facecolor=SURFACE_COLOR, metadata={"Date": None})
    png_path = path.with_suffix(".png")
    figure.savefig(png_path, facecolor=SURFACE_COLOR, dpi=PNG_DPI)


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
    peak_memory = metric_table(medians, "peak_memory_mb", all_corpora, variant_names)
    acceptance = metric_table(medians, "accept_pct", all_corpora, variant_names)

    # Every variant changes one thing from the variant before it, so its figures compare the two, such as
    # nocopy against baseline in results/figures/nocopy/.
    for previous, current in itertools.pairwise(variant_names):
        pair = [previous, current]
        pair_dir = FIGURES_DIR / current
        pair_dir.mkdir(parents=True, exist_ok=True)
        grouped_bars(
            pair_dir / "drafting.svg",
            statistics,
            "draft_us_per_token",
            all_corpora,
            pair,
            "Latency (µs / token)",
            unit_divisor=1,
        )
        grouped_bars(
            pair_dir / "load.svg",
            statistics,
            "load_ms",
            CORPUS_NAMES,
            pair,
            "Static Cache Load Time (s)",
            unit_divisor=1000,
        )
        # The memory figure shows the whole peak, so its bars at 0 MB hold the context and dynamic caches.
        grouped_bars(
            pair_dir / "memory.svg",
            statistics,
            "peak_memory_mb",
            all_corpora,
            pair,
            "Peak Memory (GB)",
            unit_divisor=1000,
        )

    followers_rows = read_rows(FOLLOWERS_PATH, FollowersRow)
    followers_cdf(FIGURES_DIR / "followers.svg", followers_rows)

    caches = pl.DataFrame([row.model_dump() for row in create_rows])
    cache_files = caches.select(
        "cache_format",
        pl.col("corpus").replace_strict(LABELS),
        (pl.col("cache_bytes") / BYTES_PER_MB).alias("file (MB)"),
        (pl.col("peak_rss_bytes") / BYTES_PER_MB).alias("peak memory of llama-lookup-create (MB)"),
    )
    memory_gib = machine.memory_bytes / 2**30
    machine_line = f"{machine.cpu}, {machine.cores} cores, {memory_gib:.0f} GiB, {machine.os}"
    run_numbers = stats["run"]
    run_count = run_numbers.n_unique()
    sections = [
        f"Machine: {machine_line}. Every value is the median of {run_count} runs of `llama-lookup-stats`.\n",
        markdown("Drafting time per drafted token (µs)", drafting, 2),
        markdown("Static cache load time (ms)", load, 0),
        markdown("Static cache memory (MB)", memory, 0),
        markdown("Peak memory (MB)", peak_memory, 0),
        markdown("Accepted drafted tokens (%)", acceptance, 3),
        markdown("Static cache files", cache_files, 0),
    ]
    TABLES_PATH.write_text("\n".join(sections))
    print(f"wrote {TABLES_PATH.relative_to(ROOT)} and {FIGURES_DIR.relative_to(ROOT)}/", flush=True)
