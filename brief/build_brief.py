"""
Builds brief/brief.tex from outputs/key_numbers.json (so every number in the text comes from the analysis)
and compiles it to brief/brief.pdf.   Run from the repo root:  python brief/build_brief.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
K = json.loads((ROOT / "outputs" / "key_numbers.json").read_text())
S = {s["scenario"]: s for s in K["scenarios"]}

import sys

sys.path.insert(0, str(ROOT / "model"))
from aicd_model import load_inputs  # noqa: E402

INP = load_inputs()


def sc(prefix: str) -> dict:
    return next(v for k, v in S.items() if k.startswith(prefix))


base = K["base"]
printed = K["printed"]
rec = K["regression"]
mc_a = K["monte_carlo"]["A_symmetric_25pct"]

single = [
    sc("Complexity: leave out")["headline"],
    sc("Complexity: median")["headline"],
    sc("Complexity: no adj")["headline"],
    sc("Compliance roles")["headline"],
    sc("Other-staff hours: 60")["headline"],
    sc("Other-staff hours: 40")["headline"],
    sc("No overhead")["headline"],
    sc("IT share")["headline"],
]
combined = sc("Combined")
cuts = [printed["m3"] * 0.25, printed["m1"] * 0.25, combined["25pct_cut_bn"], base["headline"] * 0.25]

tok = {
    "M1": f"{base['m1']:.0f}",
    "M2": f"{base['m2']:.0f}",
    "M3": f"{base['m3']:.0f}",
    "HEAD": f"{base['headline']:.0f}",
    "HEADPR": f"{printed['headline_avg_of_printed']:.0f}",
    "M3GAP": f"{base['m3'] - printed['m3']:.0f}",
    "OSLAB": f"{K['os_labour']:.0f}",
    "SHARE_BASELINE": f"{100 * K['tornado_top3'][0]['elasticity']:.0f}",
    "IT24_M3": f"{sc('IT share')['m3']:.0f}",
    "IT24_HEAD": f"{sc('IT share')['headline']:.0f}",
    "NOTIONAL_SHARE": f"{100 * K['notional_share_of_cx_sum']:.0f}",
    "CX_EXCL_M1": f"{sc('Complexity: leave out')['m1']:.0f}",
    "CX_EXCL_HEAD": f"{sc('Complexity: leave out')['headline']:.0f}",
    "CX_EXCL_PCT": f"{100 * K['cx_mean_excl_notional']:.0f}",
    "OS_SHARE": f"{100 * K['other_staff_share_of_m3_total']:.0f}",
    "H60_HEAD": f"{sc('Other-staff hours: 60')['headline']:.0f}",
    "H60_M3": f"{sc('Other-staff hours: 60')['m3']:.0f}",
    "HOURS130": f"{K['hours_for_m3_equals_printed_130']:.0f}",
    "SINGLE_LO": f"{min(single):.0f}",
    "SINGLE_HI": f"{max(single):.0f}",
    "COMB": f"{combined['headline']:.0f}",
    "MC_P10": f"{mc_a['p10']:.0f}",
    "MC_P90": f"{mc_a['p90']:.0f}",
    "CUT_LO": f"{min(cuts):.0f}",
    "CUT_HI": f"{max(cuts):.0f}",
    "CUT_HEAD": f"{base['headline'] * 0.25:.0f}",
    "REG_SE": f"{rec['implied_se']:.1f}",
    "REG_LO": f"{rec['ci95_coef'][0]:.0f}",
    "REG_HI": f"{rec['ci95_coef'][1]:.1f}",
    "FORE_LOSS": f"{max(rec['foregone_ci95_bn']):.1f}",
    "FORE_GAIN": f"{abs(min(rec['foregone_ci95_bn'])):.1f}",
    "ITEMS_SUM_ALL": f"{base['m3_total_all_levels']:.0f}",
    "HOURS58": f"{58e9 / (INP['os_workers'] * INP['os_wage']):.0f}",
    "PRINT_SPAN": f"{printed['m1'] - printed['m3']:.0f}",
    "ALT_SPAN": f"{base['headline'] - combined['headline']:.0f}",
}

TEX = r"""
\documentclass[10pt,a4paper]{article}
\usepackage[margin=0.72in,top=0.6in,bottom=0.6in]{geometry}
\usepackage{graphicx,booktabs,enumitem,xcolor,amsmath}
\usepackage[hidelinks]{hyperref}
\usepackage{parskip}
\pagestyle{empty}
\setlist{itemsep=1.5pt,topsep=2pt,leftmargin=1.2em}
\definecolor{ink2}{HTML}{52514E}
\newcommand{\hd}[1]{\par\vspace{3pt}{\large\bfseries #1}\par\vspace{-2pt}}
\begin{document}

{\LARGE\bfseries How much does each assumption matter?}\\[2pt]
{\large A sensitivity exercise on the AICD/Mandala estimate of Commonwealth compliance costs}\\[2pt]
{\small\color{ink2}Laural Alex Jacob \;|\; October 2026 \;|\; An independent exercise using published figures. Not affiliated with Mandala or the AICD. Model and code: github.com/laj07/aicd-sensitivity}

\hd{Why I looked at this}
I read Mandala's report for the AICD (\emph{\$160 billion and counting}, Nov 2025) and wanted to understand how the headline is put together. I build and test quantitative models, and the best way I know to understand an estimate is to rebuild it and see which inputs move it. This note records what I learned. It uses only the report's published figures, and I would welcome corrections where I have misread the method.

\hd{What I did}
I rebuilt the three methods from the inputs printed on pp.\ 27, 39 and 40, in Excel with live formulas and in Python, and cross-checked the result in R; tests confirm they agree. I then moved each input by 20\%, re-ran the model under named alternative choices, ran a Monte Carlo with stated ranges, and backed the uncertainty in the investment regression out of its p-value. Every input is recorded with its page number in \texttt{data/inputs.csv} so it can be checked against the slides.

\hd{What I found}
The order of magnitude was stable across everything I tried: the lowest case I computed is still \$@@COMB@@B a year.
\begin{itemize}
\item \textbf{The headline rebuilds closely.} The report's formulas on its printed inputs give \$@@M1@@B, \$@@M2@@B and \$@@M3@@B (printed: \$190B, \$150B and about \$130B), averaging \$@@HEAD@@B (printed: \$159B). Method 3 matches once the 96 million hours the report excludes are removed.
\item \textbf{Methods 1 and 2 build on the same 2013 estimate} of \$65B, as the report describes, so @@SHARE_BASELINE@@\% of the headline moves with that one figure. Method 3 is built up from 2024 inputs and is the lowest of the three.
\item \textbf{Two inputs carry more weight than the others.} The +35\% complexity multiplier averages six metrics, and the largest, notional amendments (+141\%), is @@NOTIONAL_SHARE@@\% of their combined change; without it Method 1 is \$@@CX_EXCL_M1@@B and the headline \$@@CX_EXCL_HEAD@@B. In Method 3, ordinary staff time is @@OS_SHARE@@\% of the line items, at 87 hours a worker a year; at 60 hours the headline is \$@@H60_HEAD@@B.
\item \textbf{Other reasonable choices} move the headline between \$@@SINGLE_LO@@B and \$@@SINGLE_HI@@B one at a time, and to \$@@COMB@@B with four together. Letting the main drivers vary 25\% either way gives an 80\% range of \$@@MC_P10@@B to \$@@MC_P90@@B.
\item \textbf{A 25\% cut is worth \$@@CUT_LO@@B to \$@@CUT_HI@@B} depending on method and choices, against \$@@CUT_HEAD@@B at the headline. A percentage target is less sensitive to these choices than a dollar figure.
\end{itemize}

\begin{center}
\includegraphics[width=0.78\linewidth]{../outputs/figs/fig3_scenarios.png}
\end{center}

\hd{Questions this raised}
These are for someone who knows the method better than I do.
\begin{enumerate}
\item \textbf{The IT share.} The IT line uses 30\% of \$135B, giving \$41B, while the source column describes a 24\% share (the average of 30\% from stakeholder insights and 17\% from the US banking survey). At 24\% Method 3 is \$@@IT24_M3@@B and the headline \$@@IT24_HEAD@@B. I may be misreading the source column, so I would value knowing which share is intended.
\item \textbf{The 87 hours.} It comes from a small-business survey (9.3 hours per business per week, shared across small-business employees) and is applied to all 14.3 million workers. Given how much of Method 3 rests on it, I was curious how the team thinks about its range.
\item \textbf{The investment result.} The coefficient of $-22.4$ with $p=0.09$ implies a standard error of about @@REG_SE@@ and a 95\% interval from $@@REG_LO@@$ to $+@@REG_HI@@$. At the ends of that interval, foregone investment ranges from a loss of \$@@FORE_LOSS@@B to a gain of \$@@FORE_GAIN@@B, against the printed \$10.4B. The report describes the result as marginal, which fits; I wondered how it is weighed alongside the direct cost estimate.
\item \textbf{Costs and benefits.} The estimate counts costs. I was curious how the team thinks about pairing it with the benefits side, such as the protections that followed the Royal Commissions.
\end{enumerate}

\begin{center}
\includegraphics[width=0.78\linewidth]{../outputs/figs/fig2_tornado.png}
\end{center}

\hd{Limits}
I tested the departures the arithmetic allows, not upward cases such as state and local regulation, which the report leaves out. Hours of 60 and 40 and no overhead on staff time are my own choices, not figures from the report; the 24\% IT share is the one in the report's own source column. The employment-growth adjustment uses the report's 30\% for 2010--24 and should be checked against ABS data for 2013--24. The regression uses non-public data and I could not replicate it; the interval is backed out of the printed p-value.

\hd{A related question from my own work}
CallFlag, a tool I built that was a finalist in the Forward: AI in Business Hackathon, flags National Credit Code obligations during bank hardship calls, where a wrong flag starts a 21-day legal clock. It faces a version of the same trade-off at call level: flag only when the evidence passes $c_{\mathrm{fp}}/(c_{\mathrm{fp}}+c_{\mathrm{miss}})$, where $c_{\mathrm{fp}}$ is the cost of a false flag and $c_{\mathrm{miss}}$ the cost of a miss. Your report made me curious how that trade-off looks at the scale of the economy.

\end{document}
"""

# the 'gain' sentence needs clean wording; build it explicitly
tex = TEX.replace(
    "foregone investment would range from \\$@@FORE_LO@@B down to a \\$@@FORE_HI@@B ... gain",
    "foregone investment would range from a loss of \\$@@FORE_LOSS@@B to a gain of \\$@@FORE_GAIN@@B",
)
for k, v in tok.items():
    tex = tex.replace(f"@@{k}@@", v)
assert "@@" not in tex, "unfilled token"
(ROOT / "brief" / "brief.tex").write_text(tex)

if shutil.which("pdflatex"):
    for _ in range(2):
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "brief.tex"],
            cwd=ROOT / "brief",
            check=True,
            capture_output=True,
        )
    out = subprocess.run(["pdfinfo", "brief.pdf"], cwd=ROOT / "brief", capture_output=True, text=True).stdout
    print([l for l in out.splitlines() if l.startswith("Pages")])
