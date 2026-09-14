"""Check the refactoring against the original script.

Week 7 assignment — Reproducible Research. Jakub Ryłow

The point of a refactoring is that it changes the code and not the answer, so
the claim needs a test rather than a promise. Below, the original script's
arithmetic is reproduced as literally as Python allows - the same hard-coded
three countries, the same repeated blocks, the same order of operations - and
its output is compared cell by cell with `task_intensity.py`.

    python verify_against_original.py

Exits non-zero if anything disagrees by more than 1e-12 relative.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from task_intensity_Rylow import DATA_DIR, task_intensity_table

TOL = 1e-12


def original_computation(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """The original script, transcribed, for Belgium, Spain and Poland."""
    path = data_dir / "Eurostat_employment_isco.xlsx"
    task_data = pd.read_csv(data_dir / "onet_tasks.csv")

    isco1 = pd.read_excel(path, sheet_name="ISCO1")
    isco2 = pd.read_excel(path, sheet_name="ISCO2")
    isco3 = pd.read_excel(path, sheet_name="ISCO3")
    isco4 = pd.read_excel(path, sheet_name="ISCO4")
    isco5 = pd.read_excel(path, sheet_name="ISCO5")
    isco6 = pd.read_excel(path, sheet_name="ISCO6")
    isco7 = pd.read_excel(path, sheet_name="ISCO7")
    isco8 = pd.read_excel(path, sheet_name="ISCO8")
    isco9 = pd.read_excel(path, sheet_name="ISCO9")

    total_Belgium = (
        isco1["Belgium"] + isco2["Belgium"] + isco3["Belgium"] + isco4["Belgium"]
        + isco5["Belgium"] + isco6["Belgium"] + isco7["Belgium"] + isco8["Belgium"]
        + isco9["Belgium"]
    )
    total_Spain = (
        isco1["Spain"] + isco2["Spain"] + isco3["Spain"] + isco4["Spain"]
        + isco5["Spain"] + isco6["Spain"] + isco7["Spain"] + isco8["Spain"]
        + isco9["Spain"]
    )
    total_Poland = (
        isco1["Poland"] + isco2["Poland"] + isco3["Poland"] + isco4["Poland"]
        + isco5["Poland"] + isco6["Poland"] + isco7["Poland"] + isco8["Poland"]
        + isco9["Poland"]
    )

    isco1["ISCO"] = 1
    isco2["ISCO"] = 2
    isco3["ISCO"] = 3
    isco4["ISCO"] = 4
    isco5["ISCO"] = 5
    isco6["ISCO"] = 6
    isco7["ISCO"] = 7
    isco8["ISCO"] = 8
    isco9["ISCO"] = 9

    all_data = pd.concat(
        [isco1, isco2, isco3, isco4, isco5, isco6, isco7, isco8, isco9],
        ignore_index=True,
    )
    all_data["total_Belgium"] = pd.concat([total_Belgium] * 9, ignore_index=True)
    all_data["total_Spain"] = pd.concat([total_Spain] * 9, ignore_index=True)
    all_data["total_Poland"] = pd.concat([total_Poland] * 9, ignore_index=True)

    all_data["share_Belgium"] = all_data["Belgium"] / all_data["total_Belgium"]
    all_data["share_Spain"] = all_data["Spain"] / all_data["total_Spain"]
    all_data["share_Poland"] = all_data["Poland"] / all_data["total_Poland"]

    task_data["isco08_1dig"] = task_data["isco08"].astype(str).str[:1].astype(int)
    aggdata = task_data.groupby(["isco08_1dig"]).mean().drop(columns=["isco08"])

    combined = pd.merge(
        all_data, aggdata, left_on="ISCO", right_on="isco08_1dig", how="left"
    )

    for item in ("t_4A2a4", "t_4A2b2", "t_4A4a1"):
        for country in ("Belgium", "Poland", "Spain"):
            weights = combined[f"share_{country}"]
            temp_mean = np.average(combined[item], weights=weights)
            temp_sd = np.sqrt(
                np.average((combined[item] - temp_mean) ** 2, weights=weights)
            )
            combined[f"std_{country}_{item}"] = (
                combined[item] - temp_mean
            ) / temp_sd

    for country in ("Belgium", "Poland", "Spain"):
        combined[f"{country}_NRCA"] = (
            combined[f"std_{country}_t_4A2a4"]
            + combined[f"std_{country}_t_4A2b2"]
            + combined[f"std_{country}_t_4A4a1"]
        )
        weights = combined[f"share_{country}"]
        temp_mean = np.average(combined[f"{country}_NRCA"], weights=weights)
        temp_sd = np.sqrt(
            np.average(
                (combined[f"{country}_NRCA"] - temp_mean) ** 2, weights=weights
            )
        )
        combined[f"std_{country}_NRCA"] = (
            combined[f"{country}_NRCA"] - temp_mean
        ) / temp_sd
        combined[f"multip_{country}_NRCA"] = (
            combined[f"std_{country}_NRCA"] * combined[f"share_{country}"]
        )

    out = {}
    for country in ("Belgium", "Spain", "Poland"):
        agg = combined.groupby("TIME")[f"multip_{country}_NRCA"].sum()
        out[country] = agg
    return pd.DataFrame(out)


def main() -> int:
    original = original_computation()
    refactored = task_intensity_table(
        countries=["Belgium", "Spain", "Poland"], category="NRCA"
    )

    print(f"original:   {original.shape[0]} quarters x {original.shape[1]} countries")
    print(f"refactored: {refactored.shape[0]} quarters x {refactored.shape[1]} countries")

    refactored = refactored.reindex(index=original.index, columns=original.columns)
    diff = (refactored - original).abs()
    scale = original.abs().clip(lower=1e-30)
    worst_abs = float(diff.max().max())
    worst_rel = float((diff / scale).max().max())

    print(f"\nlargest absolute difference: {worst_abs:.3e}")
    print(f"largest relative difference: {worst_rel:.3e}")

    print("\nfirst and last three quarters, refactored:")
    print(pd.concat([refactored.head(3), refactored.tail(3)]).round(6).to_string())

    if worst_rel > TOL:
        print("\nDISAGREEMENT: the refactoring changed the answer.")
        return 1
    print(f"\nAgreement within {TOL:g} relative on every cell.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
