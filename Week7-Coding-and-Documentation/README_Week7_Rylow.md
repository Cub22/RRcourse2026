# Week 7 — Coding and documentation

Jakub Ryłow

## Files

`task_intensity_Rylow.py` — the cleaned version of the class script.
`verify_against_original_Rylow.py` — reproduces the original arithmetic and
compares it with the cleaned version, cell by cell.

Both expect the course `Data/` folder two levels up, or a path given with
`--data-dir`.

```sh
python verify_against_original_Rylow.py          # does the refactoring change the answer?
python task_intensity_Rylow.py --list            # countries and task categories available
python task_intensity_Rylow.py                   # every country, non-routine cognitive analytical
python task_intensity_Rylow.py --category RM --countries Poland Spain --plot rm.png
```

## Does it still give the same answer?

Yes, and that is checked rather than claimed. `verify_against_original_Rylow.py`
transcribes the original's hard-coded blocks for Belgium, Spain and Poland and
compares them with the refactored output:

```
largest absolute difference: 1.110e-16
largest relative difference: 2.450e-13
Agreement within 1e-12 relative on every cell.
```

The residual is floating-point summation order, not a change in method.

## What was changed, and why

**The three countries became an argument.** The original wrote out a nine-term
addition per country to get employment totals, then repeated each total nine
times to align it with the stacked frame. A `groupby("TIME").transform("sum")`
does this for any country, and the list of countries is now read off the
spreadsheet's columns — so the script runs for all nine countries in the file
rather than the three that were typed in. The original's closing comment asked
for exactly this.

**The standardisation was written once.** Standardising a task item against the
employment distribution appeared nine times (three items × three countries) and
then three more times for the summed index, each a four-line block differing
only in two names. It is now one function, `weighted_standardise`. This is where
the original was most exposed: a block that mentions `Belgium` four times and
`share_Poland` once is a bug that produces plausible numbers and no error.

**The task category became data.** The three O*NET codes for non-routine
cognitive analytical tasks were spelled out in the arithmetic. They now sit in
`TASK_CATEGORIES`, together with the routine manual set that the original
suggested in a comment. Adding a category is adding a dictionary entry; nothing
in the computation mentions a specific task.

**The absolute path is gone.** The original opened with
`setwd("Z:\\File folders\\Teaching\\...")`, which is the one line guaranteed not
to run on anyone else's machine. Paths are now relative to the script, with a
`--data-dir` override.

**Failures are now loud.** An unknown country, an unknown category, or a task
column missing from the data file raises with a message naming what is
available, instead of a `KeyError` on a constructed column name several steps
later.

**Comments say why, not what.** The original's comments narrated the mechanics
("this gives us one large file"). The docstrings here record the substantive
choices instead — in particular that task scores are standardised with respect
to the workforce rather than treating the nine occupation groups as equals,
which is an assumption a reader might want to disagree with and could not
previously see.

## What was deliberately not changed

The method itself, including the double standardisation, which is in the
Acemoglu–Autor framework the original cites. The output is also still a plain
table rather than a report; `--out` writes CSV and `--plot` writes a figure, so
the numbers can feed a Quarto document without this script knowing about it.
