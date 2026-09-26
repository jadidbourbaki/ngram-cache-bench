"""Draw the figures and write the markdown tables of results/ from the benchmark CSV files."""

from __future__ import annotations

import itertools
from pathlib import Path

import matplotlib
import polars as pl
from matplotlib.figure import Figure
from matplotlib.ticker import LogFormatterSciNotation, LogLocator, NullFormatter

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
# The size of the WikiText-103 training text each static cache was built from.
X_AXIS_TITLE = "Corpus Size (MB)"
METRICS = ["draft_us_per_token", "load_ms", "accept_pct", "cache_memory_mb"]

# A fixed salt gives the SVG elements the same ids on every run, so an unchanged figure has an unchanged file.
matplotlib.rcParams["svg.hashsalt"] = "42"
# Figures follow the look of a USENIX systems paper: the Times-like STIX serif that ships with matplotlib, a
# closed frame, and inward ticks. The numeric y axis repeats its ticks on the right, where a reader of the 541 MB
# points reads their values. The categorical x axis has ticks at the bottom only.
matplotlib.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["STIXGeneral"],
        "mathtext.fontset": "stix",
        # SVG figures keep their text as text, so a browser draws it with a hinted serif as sharp as the page text.
        "svg.fonttype": "none",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.linewidth": 1.0,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": False,
        "ytick.right": True,
        "xtick.major.size": 4,
        "ytick.major.size": 4,
        "ytick.minor.size": 2.5,
        "xtick.major.width": 1.0,
        "ytick.major.width": 1.0,
        "ytick.minor.width": 0.8,
        "legend.fontsize": 11,
        "legend.handlelength": 1.2,
        "legend.borderpad": 0.4,
        "patch.linewidth": 0.8,
        "legend.frameon": True,
        "legend.fancybox": False,
        "legend.edgecolor": "black",
        "legend.framealpha": 1,
    }
)
# A figure 4.5 inches wide displays at 432 px in a browser without scaling, where 11 point text is 15 px. Scaled
# to the 3.33 inch column of a two-column USENIX paper, the same text becomes 8.1 point.
FIGURE_SIZE_INCHES = (4.5, 3.0)
PNG_DPI = 300
# Markers follow the variant in the order of variants.tsv: an open black circle for the first and a filled black
# circle for the second.
MARKERS = ["o", "o", "s", "^"]
MARKER_COLOR = "#000000"
MARKER_FACE_COLORS = ["none", "#000000", "#000000", "#000000"]
MARKER_SIZE = 5.5
# Every error bar is ANSI red, so the ranges stand out against both markers.
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


def grouped_points(
    path: Path,
    statistics: dict[str, pl.DataFrame],
    metric: str,
    corpora: list[str],
    variant_names: list[str],
    ylabel: str,
    log_scale: bool,
) -> None:
    """Draw the median of each variant as a point and the fastest to slowest run as a vertical line."""
    tables = {name: metric_table(table, metric, corpora, variant_names) for name, table in statistics.items()}
    figure = Figure(figsize=FIGURE_SIZE_INCHES, facecolor=SURFACE_COLOR)
    axes = figure.add_subplot()
    axes.set_facecolor(SURFACE_COLOR)
    # Every variant sits on its corpus tick, so the points of one corpus share one vertical line.
    positions = list(range(len(corpora)))
    fastest_runs = tables["min"].select(variant_names)
    slowest_runs = tables["max"].select(variant_names)
    column_minimums = fastest_runs.min()
    column_maximums = slowest_runs.max()
    lowest = min(column_minimums.row(0))
    highest = max(column_maximums.row(0))
    for index, name in enumerate(variant_names):
        median_column = tables["median"][name]
        minimum_column = tables["min"][name]
        maximum_column = tables["max"][name]
        medians = median_column.to_list()
        minimums = minimum_column.to_list()
        maximums = maximum_column.to_list()
        below = [median - minimum for median, minimum in zip(medians, minimums, strict=True)]
        above = [maximum - median for median, maximum in zip(medians, maximums, strict=True)]
        container = axes.errorbar(
            positions,
            medians,
            yerr=[below, above],
            marker=MARKERS[index],
            linestyle="none",
            markersize=MARKER_SIZE,
            color=MARKER_COLOR,
            markerfacecolor=MARKER_FACE_COLORS[index],
            markeredgewidth=1.0,
            ecolor=ERROR_BAR_COLOR,
            elinewidth=1.2,
            capsize=5,
            capthick=1.2,
            label=name,
            zorder=3,
        )
        # errorbar draws the markers over the ranges, so we lift the ranges above the markers. A range smaller
        # than its marker, such as 3.95 to 4.13 µs, then shows as a red line across the marker.
        caplines = container.lines[1]
        barlines = container.lines[2]
        for artist in [*caplines, *barlines]:
            artist.set_zorder(4)
    axes.set_xticks(positions)
    axes.set_xticklabels([AXIS_LABELS[corpus] for corpus in corpora])
    axes.set_xlabel(X_AXIS_TITLE, color=TEXT_COLOR)
    axes.set_ylabel(ylabel, color=TEXT_COLOR)
    if log_scale:
        # A log axis keeps a 2 µs point and a 165 µs point readable on one figure.
        axes.set_yscale("log")
        # The axis leaves a factor of 2 below the fastest run and above the slowest run, so runs of 1.78 and
        # 310 µs give 0.89 to 620 µs, and runs of 0.72 and 6.1 µs give 0.36 to 12 µs.
        axes.set_ylim(lowest / 2, highest * 2)
        # Major ticks sit at powers of ten and read 10^0, 10^1, and 10^2, so the labels show that the axis is
        # logarithmic. Minor ticks mark 2 to 9 times each power of ten without labels.
        decade_locator = LogLocator(base=10)
        in_between_locator = LogLocator(base=10, subs=(2, 3, 4, 5, 6, 7, 8, 9))
        axes.yaxis.set_major_locator(decade_locator)
        axes.yaxis.set_minor_locator(in_between_locator)
        axes.yaxis.set_major_formatter(LogFormatterSciNotation(base=10))
        axes.yaxis.set_minor_formatter(NullFormatter())
    else:
        axes.set_ylim(0, highest * 1.1)
    axes.grid(axis="y", which="major", color=GRID_COLOR, linestyle="-", linewidth=0.8, zorder=0)
    # The corpora are categories, so only the log axis carries minor ticks.
    axes.tick_params(axis="x", which="minor", bottom=False, top=False)
    # matplotlib places the legend where it covers the fewest points, since a fixed corner can hide data.
    axes.legend(loc="best")
    figure.tight_layout(pad=0.3)
    figure.savefig(path, facecolor=SURFACE_COLOR, metadata={"Date": None})
    # GitHub renders PNG images in pull request descriptions, so every figure also gets a PNG copy.
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
    acceptance = metric_table(medians, "accept_pct", all_corpora, variant_names)

    # Every variant changes one thing from the variant before it, so its figures compare the two, such as
    # nocopy against baseline in results/figures/nocopy/.
    for previous, current in itertools.pairwise(variant_names):
        pair = [previous, current]
        pair_dir = FIGURES_DIR / current
        pair_dir.mkdir(parents=True, exist_ok=True)
        grouped_points(
            pair_dir / "drafting.svg",
            statistics,
            "draft_us_per_token",
            all_corpora,
            pair,
            "Latency (µs / token)",
            log_scale=True,
        )
        grouped_points(
            pair_dir / "load.svg",
            statistics,
            "load_ms",
            CORPUS_NAMES,
            pair,
            "Static Cache Load Time (ms)",
            log_scale=False,
        )
        grouped_points(
            pair_dir / "memory.svg",
            statistics,
            "cache_memory_mb",
            CORPUS_NAMES,
            pair,
            "Static Cache Memory (MB)",
            log_scale=False,
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
    run_numbers = stats["run"]
    run_count = run_numbers.n_unique()
    sections = [
        f"Machine: {machine_line}. Every value is the median of {run_count} runs of `llama-lookup-stats`.\n",
        markdown("Drafting time per drafted token (µs)", drafting, 2),
        markdown("Static cache load time (ms)", load, 0),
        markdown("Static cache memory (MB)", memory, 0),
        markdown("Accepted drafted tokens (%)", acceptance, 3),
        markdown("Static cache files", cache_files, 0),
    ]
    TABLES_PATH.write_text("\n".join(sections))
    print(f"wrote {TABLES_PATH.relative_to(ROOT)} and {FIGURES_DIR.relative_to(ROOT)}/", flush=True)
