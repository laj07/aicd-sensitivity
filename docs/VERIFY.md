# Cross-check list

Work through this top to bottom with the report PDF open alongside:
https://www.aicd.com.au/content/dam/aicd/pdf/news-media/research/2025/economic-cost-of-regulatory-complexity-report.pdf

Page numbers are the slide footers in the PDF.

## A. Inputs against the source (`data/inputs.csv`)

The inputs were read from a text extraction of the PDF, so this check matters most. Tick each one.

| # | Check | Page | What to see |
|---|---|---|---|
| 1 | 2013 estimate $65B, 4.2% of GDP | 27 | Chart labels "$65B (4.2% of GDP)", "$113B", "$159B (5.8% of GDP)" |
| 2 | Three methods averaged | 27 | "This estimate averages three approaches" |
| 3 | $113B base, +24% volume, +35% complexity | 39 | Pages 160,000 (2013) to 199,000 (2024) |
| 4 | Six complexity metrics | 39 | +141%, +40%, +23%, +22%, +7%, -23% |
| 5 | CPI +35%; roles 30,000 to 52,000 | 39 | "$88B" intermediate figure |
| 6 | Method 3 table, every row | 40 | Workers, FTE 75%, salaries, 23% and 43% time shares, 87 hours, 14.3M workers, $51/hour, $135B IT x 30%, $823M / 78%, 1% of GSP |
| 7 | Regression | 42 | Coefficient -22.4, p = 0.09, "moderately unstable across subsamples" |
| 8 | Printed Method 1 and 2 results | 39 | Chart labels "$190B" and "$150B" |
| 9 | Printed Method 3 result | 40 | "~$130B" for the Commonwealth |
| 10 | 25% cut by 2030 and the $10.4B foregone investment | 26, 42 | Recommendation and printed estimate |

Also confirm these p. 40 details, which the model now uses: the 87 hours is (9.3 hours per small business per week x 52 x 925,758 businesses) / 5,164,600 small-business employees; the table says it "excludes 96,000,000 compliance, legal, audit hours" (`os_excl`); the IT row says 30% but its source column says 24%, the average of 30% and 17%.

## B. Interpretations to decide on

1. "$2.7B GDP" (pp. 39, 40) read as $2.7 trillion. Check: 4.2% x $2.7T = $113.4B, matching the printed $113B.
2. p. 40 says overhead is "75% of $8B"; I used 75% of the labour line, which gives the printed $4B.
3. The sum of Method 3's printed lines ($160.9B) is treated as all levels of government, with $27B state cost subtracted to reach the Commonwealth figure (~$134B printed lines, ~$133B recomputed, against "~$130B"). Check the p. 40 wording.
3a. The IT row: the label says 30% (giving the printed $41B) and the source column says 24%. The brief's first question asks which is intended. **If the PDF resolves it, delete or reword that question.**
4. The report prints "+74%" for roles; 52,000 / 30,000 is +73.3%. I used the counts.
5. The p-value is treated as two-sided with a normal approximation.
6. `emp_growth` = 30% is the report's labour-market growth for 2010-24 (p. 21). Replace it with ABS employment growth for 2013-24 if you can.

## C. Claims in the brief and where each comes from

| Claim | Source in repo |
|---|---|
| $190B / $152B / $133B, average $159B | `outputs/tables/reconciliation_methods.csv`; Excel `Model` sheet; `Rscript analysis/replicate.R` |
| Printed rounded figures average $157B; the printed headline is $159B | `(190+150+130)/3` |
| 72% of the headline moves with the 2013 baseline | `outputs/tables/tornado_one_at_a_time.csv`, elasticity 0.72 |
| Notional amendments are 67% of the six metrics' combined change | `key_numbers.json`, `notional_share_of_cx_sum`; 141 / 210 |
| Without it Method 1 is $161B, headline $149B | `outputs/tables/scenarios.csv` |
| 64% of Method 3's line items is other-staff time | Excel `Reconciliation!C18` |
| 60 hours gives a $147B headline | `scenarios.csv` |
| $139B to $156B one at a time; $123B combined | `scenarios.csv` |
| 80% range $143B to $174B | `key_numbers.json`, Monte Carlo prior A |
| 25% cut worth $31B to $48B | 25% of the printed $130B and $190B, and of the combined scenario ($123B) |
| Regression interval -48.3 to +3.5 | Excel `Regression` sheet; `key_numbers.json`; the R script |

## D. Things only you can confirm

1. **CallFlag.** The brief says it is a tool you built, a finalist in the Forward: AI in Business Hackathon, that flags National Credit Code obligations in bank hardship calls, where a wrong flag starts a 21-day clock. Confirm each fact.
2. **Whether to keep the CallFlag section.** It is the last section of the brief. Delete it if you prefer the brief to stay purely on the report.
3. **GitHub URL.** The brief, README, CV and cover letter say `github.com/laj07/aicd-sensitivity`. Publish the repository there, or edit the line in `brief/build_brief.py` and rebuild.
4. **Date and byline.** Check both.
5. **You can explain every number.** Be able to say in your own words why Methods 1 and 2 share a baseline, what the +35% is made of, what the 87 hours is and why 96 million hours are excluded, and what the regression interval means. If you cannot, remove that claim from your answers.

## E. Where a reader might push back

- The alternative choices (60 or 40 hours, no overhead on staff time, and the 24% IT share) lean downward; the first two are my choices and the brief says so. No upward cases were tested. If you want balance, add an upward scenario you can defend from the report.
- The "four together" scenario ($123B) stacks four lower choices. It is a stress test, not a central estimate, and the brief words it that way.
- The shared 2013 baseline is described in the report itself. The brief states it as a fact about the structure, not a flaw.
- Method 3 only reproduces with the 96 million excluded hours removed. If a reader asks, that step is on p. 40 and is in `data/inputs.csv` as `os_excl`.

## F. Re-run everything

```bash
python analysis/run_analysis.py && python excel/build_excel.py && python tests/test_model.py && python brief/build_brief.py
Rscript analysis/replicate.R
```

The R script reads the same `data/inputs.csv` and should print $190.4B, $152.1B and $133.3B for the methods, a $158.6B headline, and a regression interval of -48.3 to +3.5.
