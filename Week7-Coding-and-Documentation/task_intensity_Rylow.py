"""Task content intensity from O*NET tasks and Eurostat employment.

Week 7 assignment (Coding and documentation) — Reproducible Research.
Jakub Ryłow

What this computes
------------------
Following Autor, Levy and Murnane (2003) and Acemoglu and Autor (2011), the
intensity of a *task category* in a country's workforce at a point in time is a
weighted mean of occupation-level task scores, the weights being the share of
employment in each occupation. Scores are standardised with respect to the same
employment distribution before being added together, so that the three items of
a category contribute on a common scale.

The original script did this for three hard-coded countries and one hard-coded
task category, repeating each block of arithmetic once per country and once per
task item — around sixty lines of copy-paste in which a single mistyped country
name would be silent. Here the country and the task category are arguments. The
file ships with the two categories named in the original (non-routine cognitive
analytical, and the routine manual set listed in its closing comment), and
adding a third means adding a dictionary entry.

Reproducing the original
------------------------
`verify_against_original.py` recomputes the original's hard-coded arithmetic and
asserts that this module agrees to within 1e-12 for Belgium, Spain and Poland.
The refactoring is therefore checked rather than asserted.

Usage
-----
    python task_intensity.py                     # every country, every category
    python task_intensity.py --countries Poland Spain --category NRCA
    python task_intensity.py --list              # what is available
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "Data"
EMPLOYMENT_FILE = "Eurostat_employment_isco.xlsx"
TASK_FILE = "onet_tasks.csv"

#: One-digit ISCO-08 major groups, which are the sheets of the employment file.
ISCO_GROUPS = range(1, 10)

#: Task categories, each a set of O*NET items that are standardised and summed.
#: The labels are the O*NET element names; the codes are the columns of the
#: task file. Both categories below come from the original script - the second
#: from the comment at its end, which suggested it as an extension.
TASK_CATEGORIES: dict[str, dict[str, str]] = {
    "NRCA": {
        "t_4A2a4": "Analyzing Data or Information",
        "t_4A2b2": "Thinking Creatively",
        "t_4A4a1": "Interpreting the Meaning of Information for Others",
    },
    "RM": {
        "t_4A3a3": "Controlling Machines and Processes",
        "t_4C2d1i": "Spend Time Making Repetitive Motions",
        "t_4C3d3": "Pace Determined by Speed of Equipment",
    },
}

CATEGORY_NAMES = {
    "NRCA": "Non-routine cognitive analytical",
    "RM": "Routine manual",
}


# --- loading ---------------------------------------------------------------


def load_employment(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Employment by quarter, ISCO major group and country, in long form.

    Returns a frame indexed by nothing in particular with columns ``TIME``,
    ``ISCO`` and one column per country. The original stacked the nine sheets
    with ``rbind`` after setting ``ISCO`` by hand nine times; the loop does the
    same thing and cannot go out of step.
    """
    path = data_dir / EMPLOYMENT_FILE
    frames = []
    for group in ISCO_GROUPS:
        sheet = pd.read_excel(path, sheet_name=f"ISCO{group}")
        sheet["ISCO"] = group
        frames.append(sheet)
    return pd.concat(frames, ignore_index=True)


def available_countries(employment: pd.DataFrame) -> list[str]:
    """Country columns of the employment frame.

    Everything that is not the time index, the ISCO group, or the EU aggregate.
    Deriving this from the file is what lets the analysis run for countries the
    original never mentioned.
    """
    skip = {"TIME", "ISCO"}
    return [
        column
        for column in employment.columns
        if column not in skip and not column.startswith("European Union")
    ]


def load_task_scores(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Mean O*NET task scores per one-digit ISCO group.

    The task file is at the level of detailed occupations, already crosswalked
    to ISCO-08; the employment data is at the one-digit level, so the scores are
    averaged up to match.
    """
    tasks = pd.read_csv(data_dir / TASK_FILE)
    tasks["isco08_1dig"] = tasks["isco08"].astype(str).str[0].astype(int)
    return tasks.groupby("isco08_1dig").mean().drop(columns=["isco08"])


def employment_shares(employment: pd.DataFrame, country: str) -> pd.Series:
    """Share of the country's workers in each occupation-quarter cell.

    The denominator is the country's total employment in that quarter, summed
    over the nine ISCO groups. The original computed these totals by writing out
    a nine-term addition per country and then repeating the result nine times to
    line it up with the stacked frame; a groupby transform does it in one line
    and for any country.
    """
    if country not in employment.columns:
        raise KeyError(f"no employment data for {country!r}")
    totals = employment.groupby("TIME")[country].transform("sum")
    return employment[country] / totals


# --- the method ------------------------------------------------------------


def weighted_standardise(values: pd.Series, weights: pd.Series) -> pd.Series:
    """Standardise ``values`` using a mean and standard deviation weighted by
    ``weights``.

    This is the operation the original repeated once per task item and once per
    country. Writing it once also makes explicit that the weights are the
    employment shares, which is the substantive assumption: task scores are
    standardised with respect to the workforce, not with respect to the nine
    occupations treated as equals.
    """
    mean = np.average(values, weights=weights)
    variance = np.average((values - mean) ** 2, weights=weights)
    sd = np.sqrt(variance)
    if sd == 0:
        raise ValueError("zero weighted variance; cannot standardise")
    return (values - mean) / sd


def category_intensity(
    combined: pd.DataFrame,
    country: str,
    task_codes: list[str],
) -> pd.Series:
    """Country-level task intensity by quarter for one task category.

    Each item is standardised against the employment distribution, the items are
    summed, the sum is standardised again, and the result is aggregated to a
    country-quarter mean weighted by employment shares.
    """
    shares = combined[f"share_{country}"]

    standardised = sum(
        weighted_standardise(combined[code], shares) for code in task_codes
    )
    intensity = weighted_standardise(standardised, shares)

    weighted = intensity * shares
    return weighted.groupby(combined["TIME"]).sum()


def build_combined(
    countries: list[str],
    employment: pd.DataFrame | None = None,
    task_scores: pd.DataFrame | None = None,
    data_dir: Path = DATA_DIR,
) -> pd.DataFrame:
    """Employment, shares and task scores in one frame, ready to aggregate."""
    if employment is None:
        employment = load_employment(data_dir)
    if task_scores is None:
        task_scores = load_task_scores(data_dir)

    combined = employment.copy()
    for country in countries:
        combined[f"share_{country}"] = employment_shares(employment, country)

    return combined.merge(
        task_scores, left_on="ISCO", right_index=True, how="left"
    )


def task_intensity_table(
    countries: list[str] | None = None,
    category: str = "NRCA",
    data_dir: Path = DATA_DIR,
) -> pd.DataFrame:
    """Task intensity for several countries, one column each, quarters as rows."""
    if category not in TASK_CATEGORIES:
        raise KeyError(
            f"unknown category {category!r}; available: {sorted(TASK_CATEGORIES)}"
        )
    employment = load_employment(data_dir)
    if countries is None:
        countries = available_countries(employment)

    task_scores = load_task_scores(data_dir)
    missing = [c for c in TASK_CATEGORIES[category] if c not in task_scores.columns]
    if missing:
        raise KeyError(f"task file lacks columns {missing} needed for {category}")

    combined = build_combined(countries, employment, task_scores, data_dir)
    return pd.DataFrame(
        {
            country: category_intensity(
                combined, country, list(TASK_CATEGORIES[category])
            )
            for country in countries
        }
    )


# --- output ----------------------------------------------------------------


def plot_table(table: pd.DataFrame, category: str, out_path: Path | None = None):
    """One panel per country, shared axes, quarters on the x axis."""
    import matplotlib

    if out_path is not None:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = table.shape[1]
    columns = min(3, n)
    rows = int(np.ceil(n / columns))
    fig, axes = plt.subplots(
        rows, columns, figsize=(4 * columns, 2.6 * rows), sharex=True, sharey=True
    )
    axes = np.atleast_1d(axes).ravel()

    ticks = range(0, len(table.index), 4)
    for ax, country in zip(axes, table.columns):
        ax.plot(range(len(table.index)), table[country], linewidth=1.4)
        ax.set_title(country, fontsize=10)
        ax.set_xticks(list(ticks))
        ax.set_xticklabels(
            [table.index[i] for i in ticks], rotation=90, fontsize=7
        )
    for ax in axes[n:]:
        ax.axis("off")

    fig.suptitle(f"{CATEGORY_NAMES.get(category, category)} task intensity")
    fig.tight_layout()
    if out_path is not None:
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
    return fig


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--countries", nargs="+", default=None)
    parser.add_argument(
        "--category", default="NRCA", choices=sorted(TASK_CATEGORIES)
    )
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--out", type=Path, default=None, help="write a CSV here")
    parser.add_argument("--plot", type=Path, default=None, help="write a PNG here")
    parser.add_argument("--list", action="store_true", help="show what is available")
    args = parser.parse_args(argv)

    if args.list:
        employment = load_employment(args.data_dir)
        print("countries:", ", ".join(available_countries(employment)))
        for key, items in TASK_CATEGORIES.items():
            print(f"\n{key} - {CATEGORY_NAMES.get(key, key)}")
            for code, label in items.items():
                print(f"  {code}  {label}")
        return 0

    table = task_intensity_table(args.countries, args.category, args.data_dir)
    pd.set_option("display.width", 160)
    print(f"{CATEGORY_NAMES.get(args.category, args.category)} task intensity\n")
    print(table.round(4).to_string())

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(args.out)
        print(f"\nwritten to {args.out}")
    if args.plot is not None:
        plot_table(table, args.category, args.plot)
        print(f"figure written to {args.plot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
