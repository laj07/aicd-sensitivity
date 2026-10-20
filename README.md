# How much does each assumption matter? A sensitivity exercise on the AICD/Mandala compliance-cost estimate

An independent exercise using published figures. Not affiliated with Mandala or the AICD, and not an estimate of the true cost of regulation. I would welcome corrections where I have misread the method.

The report [*$160 billion and counting: The cost of Commonwealth regulatory complexity*](https://www.aicd.com.au/news-media/research-and-reports/economic-cost-of-regulatory-complexity) (Mandala for the AICD, November 2025) averages three methods to reach a headline of about $160 billion a year. I wanted to understand how the headline is put together, so this repository rebuilds those methods from the inputs printed in the report and tests how much each input and assumption moves the result.

**Read first:** [`brief/brief.pdf`](brief/brief.pdf) (2 pages).

## What I found

| | |
|---|---|
| Rebuilt from printed inputs | Method 1 $190B, Method 2 $152B, Method 3 $133B; average $159B (report: $190B, $150B, about $130B; average $159B) |
| Shared baseline | Methods 1 and 2 both build on the 2013 estimate of $65B, as the report describes; 72% of the headline moves with it |
| Complexity multiplier | +35% is the mean of six metrics; one (notional amendments, +141%) is 67% of their combined change. Without it the headline is $149B |
| Method 3 | 64% of its line items are ordinary staff time at 87 hours a worker (the 87 comes from a small-business survey applied to all workers). It reproduces once the 96 million excluded hours on p. 40 are removed. The IT line uses 30%, while the source column describes 24%; at 24% the headline is $156B |
| Range | One alternative choice at a time: $139B to $156B. Four together: $123B. Symmetric 25% uncertainty on the main drivers: 80% range $143B to $174B |
| 25% cut by 2030 | Worth $31B to $48B depending on method and choices, against $40B at the headline |
| Investment result | p = 0.09 implies a 95% interval for the coefficient of about -48 to +3.5, which includes zero |

## Run it

```bash
pip install numpy pandas matplotlib openpyxl
python analysis/run_analysis.py     # tables, charts, outputs/key_numbers.json
python excel/build_excel.py         # excel/aicd_cost_model.xlsx (live formulas)
python tests/test_model.py          # identities + Excel-vs-Python cross-check (needs LibreOffice)
python brief/build_brief.py         # brief/brief.pdf (needs pdflatex)
Rscript analysis/replicate.R        # independent re-computation in base R; matches the Python results
```

## Layout

```
data/inputs.csv            every input, with the report page, and whether it is printed / interpreted / assumption
model/aicd_model.py        the three methods, as functions
analysis/run_analysis.py   reconciliation, one-at-a-time swings, scenarios, Monte Carlo, regression interval
analysis/replicate.R       independent re-computation of the three methods and the regression interval in base R (cross-check of the Python model)
excel/                     the same model with live formulas; sheets: Inputs, Model, Reconciliation, Scenarios, Sensitivity, Regression
tests/test_model.py        checks that the Python and Excel models agree
outputs/                   tables (csv), figures (png), key_numbers.json
brief/                     the 2-page write-up (numbers are filled in from outputs/key_numbers.json)
docs/VERIFY.md             checklist: every claim, where it comes from, how to check it
```

## Method notes

- **Inputs.** Taken from pp. 27, 39, 40 and 42 of the PDF (slide footers). GDP and GSP are printed as "$2.7B"; I read them as $2.7 trillion (flagged `interpreted`), since 4.2% of $2.7T is $113B, which matches the printed figure.
- **Scenarios.** Hours of 60 and 40 and no overhead on staff time are the author's choices, not report figures. The 24% IT share is the one in the report's own source column. The employment-growth adjustment uses the report's 30% for 2010-24 and should be checked against ABS data for 2013-24 (`emp_growth`, status `assumption`).
- **Monte Carlo.** Prior A: six uncertain drivers vary +/-25% (triangular) around the report's values. A second run, a downside-only stress test drawn from the lower alternatives, is in `outputs/` and the charts; it shows how far the headline moves if every uncertain choice goes one way. It is not an estimate.
- **Regression.** The standard error is backed out from the printed p-value assuming a two-sided normal approximation and a model linear in the compliance share. The underlying data (Revelio) are not public, so the regression cannot be replicated.

## Limits

- The analysis tests departures the arithmetic allows. It does not test upward cases, such as the state and local regulation the report excludes.
- The estimate counts costs only. It does not weigh the benefits of regulation.
- Nothing here assesses the report's recommendations. It only looks at how sensitive the cost figure is to its inputs.

## Tool for the error-cost question

`outputs/figs/fig5_error_cost_threshold.png` plots the standard decision rule behind a related question: flag only when the evidence passes cost(false flag) / (cost(false flag) + cost(miss)). It is theory only and uses no data.
