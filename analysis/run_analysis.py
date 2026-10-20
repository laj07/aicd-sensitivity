"""
Sensitivity analysis of the AICD/Mandala estimate of Commonwealth compliance cost.

Run from the repo root:   python analysis/run_analysis.py
Outputs: outputs/tables/*.csv, outputs/figs/*.png, outputs/key_numbers.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import NormalDist, median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "model"))
from aicd_model import CX_KEYS, PRINTED_ITEMS, compute, load_inputs, printed_reference  # noqa: E402

OUT_T = ROOT / "outputs" / "tables"
OUT_F = ROOT / "outputs" / "figs"
OUT_T.mkdir(parents=True, exist_ok=True)
OUT_F.mkdir(parents=True, exist_ok=True)

# Palette: reference categorical slots 1 and 2 (light mode), ink greys for text.
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#dcdcd8"
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.edgecolor": GRID,
        "axes.labelcolor": INK2,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
)



def put_title(fig, text, top=0.93):
    fig.tight_layout(rect=[0, 0, 1, top])
    fig.text(0.01, 0.985, text, ha="left", va="top", fontsize=10, color=INK)

P = load_inputs()
BASE = compute(P)
PRINTED = printed_reference(P)
KEY: dict = {}

# ---------------------------------------------------------------- 1. Reconciliation
rows = []
for k, printed in PRINTED_ITEMS.items():
    rows.append(
        {
            "line": k,
            "printed_bn": printed,
            "recomputed_bn": BASE[f"item_{k}"],
            "gap_bn": BASE[f"item_{k}"] - printed,
        }
    )
recon = pd.DataFrame(rows)
recon.to_csv(OUT_T / "reconciliation_method3_lines.csv", index=False)

meth = pd.DataFrame(
    [
        ("Method 1: volume x complexity", PRINTED["m1"], BASE["m1"]),
        ("Method 2: CPI x compliance roles", PRINTED["m2"], BASE["m2"]),
        ("Method 3: bottom-up (Commonwealth)", PRINTED["m3"], BASE["m3"]),
        ("Average of the three", PRINTED["headline_avg_of_printed"], BASE["headline"]),
    ],
    columns=["method", "printed_bn", "recomputed_bn"],
)
meth["gap_bn"] = meth.recomputed_bn - meth.printed_bn
meth.to_csv(OUT_T / "reconciliation_methods.csv", index=False)

KEY["base"] = {k: float(BASE[k]) for k in ("m1", "m2", "m3", "headline", "m3_total_all_levels", "m3_state")}
KEY["printed"] = {k: float(v) for k, v in PRINTED.items()}
KEY["other_staff_share_of_m3_total"] = float(BASE["other_staff_share_of_m3_total"])
KEY["os_labour"] = float(BASE["item_other_staff_labour"])
KEY["os_overhead"] = float(BASE["item_other_staff_overhead"])
KEY["it_systems"] = float(BASE["item_it_systems"])
KEY["os_labour_printed_formula_gap"] = float(BASE["item_other_staff_labour"] - 58.0)

# Method 1 and 2 share a baseline
KEY["shared_baseline_note"] = "Methods 1 and 2 both start from the 2013 estimate of $65B."

# Complexity multiplier composition
cx_vals = {k: P[k] for k in CX_KEYS}
KEY["cx_mean_all"] = float(np.mean(list(cx_vals.values())))
KEY["cx_mean_excl_notional"] = float(np.mean([v for k, v in cx_vals.items() if k != "cx_notional"]))
KEY["cx_median_all"] = float(np.median(list(cx_vals.values())))
KEY["notional_share_of_cx_sum"] = float(cx_vals["cx_notional"] / sum(cx_vals.values()))

# ---------------------------------------------------------------- 2. One-at-a-time swings
SWING = 0.20
D = BASE


def swing_overrides(name: str, f: float) -> dict:
    if name == "2013 baseline (moves Methods 1 and 2)":
        return {"gdp_share_2013": P["gdp_share_2013"] * f, "base_2013": P["base_2013"] * f}
    table = {
        "Volume multiplier (M1)": {"vol_mult": D["drv_vol_mult"] * f},
        "Complexity multiplier (M1)": {"cx_mult": D["drv_cx_mult"] * f},
        "CPI multiplier (M2)": {"cpi_mult": D["drv_cpi_mult"] * f},
        "Compliance-role multiplier (M2)": {"role_mult": D["drv_role_mult"] * f},
        "Hours of compliance per worker (M3)": {"os_hours": P["os_hours"] * f},
        "Average hourly wage (M3)": {"os_wage": P["os_wage"] * f},
        "Total workers (M3)": {"os_workers": P["os_workers"] * f},
        "Overhead multiplier (M3)": {"oh_mult": P["oh_mult"] * f},
        "Share of IT spend that is compliance (M3)": {"it_share": P["it_share"] * f},
        "Total IT spend (M3)": {"it_spend": P["it_spend"] * f},
        "State cost share of GSP (subtracted in M3)": {"state_share_gsp": P["state_share_gsp"] * f},
        "Compliance workers (M3)": {"cw_workers": P["cw_workers"] * f},
    }
    return table[name]


driver_names = [
    "2013 baseline (moves Methods 1 and 2)",
    "Volume multiplier (M1)",
    "Complexity multiplier (M1)",
    "CPI multiplier (M2)",
    "Compliance-role multiplier (M2)",
    "Hours of compliance per worker (M3)",
    "Average hourly wage (M3)",
    "Total workers (M3)",
    "Overhead multiplier (M3)",
    "Share of IT spend that is compliance (M3)",
    "Total IT spend (M3)",
    "State cost share of GSP (subtracted in M3)",
    "Compliance workers (M3)",
]
tor = []
for n in driver_names:
    lo = compute(P, **swing_overrides(n, 1 - SWING))["headline"]
    hi = compute(P, **swing_overrides(n, 1 + SWING))["headline"]
    tor.append(
        {
            "driver": n,
            "headline_at_minus20pct": lo,
            "headline_at_plus20pct": hi,
            "swing_bn": abs(hi - lo),
            "elasticity": ((hi - lo) / BASE["headline"]) / (2 * SWING),
        }
    )
tor = pd.DataFrame(tor).sort_values("swing_bn", ascending=False).reset_index(drop=True)
tor.to_csv(OUT_T / "tornado_one_at_a_time.csv", index=False)
KEY["tornado_top3"] = tor.head(3)[["driver", "swing_bn", "elasticity"]].to_dict("records")

GROUP = {
    "2013 baseline (moves Methods 1 and 2)": "2013 baseline (moves M1 and M2)",
    "Volume multiplier (M1)": "Volume or complexity multiplier (M1)",
    "Complexity multiplier (M1)": "Volume or complexity multiplier (M1)",
    "CPI multiplier (M2)": "CPI or compliance-role multiplier (M2)",
    "Compliance-role multiplier (M2)": "CPI or compliance-role multiplier (M2)",
    "Overhead multiplier (M3)": "Overhead multiplier (M3)",
    "Hours of compliance per worker (M3)": "Hours per worker, hourly wage or workers (M3)",
    "Average hourly wage (M3)": "Hours per worker, hourly wage or workers (M3)",
    "Total workers (M3)": "Hours per worker, hourly wage or workers (M3)",
    "Share of IT spend that is compliance (M3)": "IT spend, or compliance share of it (M3)",
    "Total IT spend (M3)": "IT spend, or compliance share of it (M3)",
    "State cost share of GSP (subtracted in M3)": "State cost share (subtracted in M3)",
    "Compliance workers (M3)": "Compliance workers (M3)",
}
tor_plot = tor.assign(driver=tor.driver.map(GROUP)).drop_duplicates("driver").reset_index(drop=True)
fig, ax = plt.subplots(figsize=(6.6, 3.1))
ypos = np.arange(len(tor_plot))[::-1]
b = BASE["headline"]
for y, r in zip(ypos, tor_plot.itertuples()):
    lo, hi = r.headline_at_minus20pct, r.headline_at_plus20pct
    ax.barh(y, lo - b, left=b, color=ORANGE, height=0.62, linewidth=0)
    ax.barh(y, hi - b, left=b, color=BLUE, height=0.62, linewidth=0)
ax.set_yticks(ypos)
ax.set_yticklabels(tor_plot.driver, fontsize=8)
ax.axvline(b, color=INK, lw=1)
ax.set_xlabel("Headline estimate (AUD billions)")
ax.grid(axis="x", color=GRID, lw=0.6)
ax.set_axisbelow(True)
from matplotlib.patches import Patch  # noqa: E402

ax.legend(
    handles=[Patch(color=ORANGE, label="Input 20% lower"), Patch(color=BLUE, label="Input 20% higher")],
    loc="lower right",
    frameon=False,
    fontsize=8,
)
put_title(fig, f"Moving each input by 20% from the base case of \\${b:.0f}B")
fig.savefig(OUT_F / "fig2_tornado.png", dpi=220)
plt.close(fig)

# ---------------------------------------------------------------- 3. Named alternatives
cx_excl = 1 + KEY["cx_mean_excl_notional"]
cx_med = 1 + KEY["cx_median_all"]
role_net = D["drv_role_mult"] / (1 + P["emp_growth"])
scen = [
    ("Report's method, recomputed from printed inputs", {}),
    ("Complexity: leave out notional amendments", {"cx_mult": cx_excl}),
    ("Complexity: median of the six metrics", {"cx_mult": cx_med}),
    ("Complexity: no adjustment", {"cx_mult": 1.0}),
    ("Compliance roles: net of employment growth", {"role_mult": role_net}),
    ("Other-staff hours: 60 instead of 87", {"os_hours": 60}),
    ("Other-staff hours: 40 instead of 87", {"os_hours": 40}),
    ("No overhead loading on other-staff time", {"os_oh_mult": 1.0}),
    ("IT share of spend: 24% (the report's footnote) instead of 30%", {"it_share": 0.24}),
    (
        "Combined: four of the lower alternatives above",
        {"cx_mult": cx_excl, "role_mult": role_net, "os_hours": 60, "it_share": 0.24},
    ),
]
srows = []
for name, ov in scen:
    r = compute(P, **ov)
    srows.append(
        {
            "scenario": name,
            "m1": r["m1"],
            "m2": r["m2"],
            "m3": r["m3"],
            "headline": r["headline"],
            "vs_reported_159": r["headline"] - P["printed_headline"],
            "25pct_cut_bn": 0.25 * r["headline"],
        }
    )
srows.append(
    {
        "scenario": "Average of the three printed (rounded) figures",
        "m1": PRINTED["m1"],
        "m2": PRINTED["m2"],
        "m3": PRINTED["m3"],
        "headline": PRINTED["headline_avg_of_printed"],
        "vs_reported_159": PRINTED["headline_avg_of_printed"] - P["printed_headline"],
        "25pct_cut_bn": 0.25 * PRINTED["headline_avg_of_printed"],
    }
)
scen_df = pd.DataFrame(srows)
scen_df.to_csv(OUT_T / "scenarios.csv", index=False)
KEY["scenarios"] = scen_df.to_dict("records")  # full precision; round only when displaying
KEY["scenario_inputs"] = {
    "cx_excl_notional": cx_excl,
    "cx_median": cx_med,
    "role_net": role_net,
    "emp_growth_assumed": P["emp_growth"],
}

fig, ax = plt.subplots(figsize=(6.6, 3.5))
sd = scen_df.iloc[::-1].reset_index(drop=True)
colors = [BLUE if i == len(sd) - 2 else "#9fb9d9" for i in range(len(sd))]  # highlight 'recomputed' row
for i, r in sd.iterrows():
    is_base = r.scenario.startswith("Report's method")
    ax.barh(i, r.headline, color=BLUE if is_base else "#9fb9d9", height=0.62, linewidth=0)
    ax.text(r.headline + 2, i, f"\\${r.headline:.0f}B", va="center", fontsize=8, color=INK)
ax.set_yticks(range(len(sd)))
ax.set_yticklabels(sd.scenario, fontsize=8)
ax.axvline(P["printed_headline"], color=ORANGE, lw=1.4)
ax.text(
    P["printed_headline"] + 1,
    len(sd) - 0.35,
    "Reported: \\$159B",
    color=ORANGE,
    fontsize=8,
    va="bottom",
)
ax.set_xlim(0, 215)
ax.set_xlabel("Headline estimate (AUD billions)")
ax.grid(axis="x", color=GRID, lw=0.6)
ax.set_axisbelow(True)
put_title(fig, "What the headline becomes under other modelling choices")
fig.savefig(OUT_F / "fig3_scenarios.png", dpi=220)
plt.close(fig)

# ---------------------------------------------------------------- 4. Monte Carlo
rng = np.random.default_rng(20261017)
N = 20_000


def tri(x, lo_f, hi_f, n):
    return rng.triangular(x * lo_f, x, x * hi_f, n)


def prior_a(n):
    return {
        "vol_mult": tri(D["drv_vol_mult"], 0.75, 1.25, n),
        "cx_mult": tri(D["drv_cx_mult"], 0.75, 1.25, n),
        "role_mult": tri(D["drv_role_mult"], 0.75, 1.25, n),
        "os_hours": tri(P["os_hours"], 0.75, 1.25, n),
        "it_share": tri(P["it_share"], 0.75, 1.25, n),
        "os_oh_mult": tri(P["oh_mult"], 0.75, 1.25, n),
    }


def prior_b(n):
    return {
        "vol_mult": tri(D["drv_vol_mult"], 0.90, 1.10, n),
        "cx_mult": rng.choice([1.0, cx_excl, cx_med, D["drv_cx_mult"]], n),
        "role_mult": rng.choice([D["drv_role_mult"], role_net], n),
        "os_hours": rng.triangular(40, 60, 87, n),
        "it_share": rng.triangular(0.15, 0.25, 0.30, n),
        "os_oh_mult": rng.triangular(1.0, 1.4, 1.75, n),
    }


def run_mc(draws, n):
    out = np.empty(n)
    for i in range(n):
        ov = {k: float(v[i]) for k, v in draws.items()}
        out[i] = compute(P, **ov)["headline"]
    return out


mc = {}
for label, fn in (("A_symmetric_25pct", prior_a), ("B_alternatives_from_report", prior_b)):
    d = fn(N)
    h = run_mc(d, N)
    ranks = pd.DataFrame({**d, "headline": h}).rank().corr()["headline"].drop("headline")
    mc[label] = {
        "draws": h,
        "p10": float(np.percentile(h, 10)),
        "median": float(np.median(h)),
        "p90": float(np.percentile(h, 90)),
        "share_at_or_above_159": float((h >= P["printed_headline"]).mean()),
        "spearman_with_headline": ranks.round(2).to_dict(),
    }
pd.DataFrame(
    {k: v["draws"] for k, v in mc.items()}
).to_csv(OUT_T / "monte_carlo_draws.csv", index=False)
KEY["monte_carlo"] = {k: {kk: vv for kk, vv in v.items() if kk != "draws"} for k, v in mc.items()}

fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.5), sharey=True, sharex=True)
titles = {
    "A_symmetric_25pct": "Prior A: uncertain inputs vary 25% either side",
    "B_alternatives_from_report": "Downside stress test: lower alternatives only",
}
for ax, (k, v) in zip(axes, mc.items()):
    ax.hist(v["draws"], bins=60, color=BLUE, alpha=0.9, linewidth=0)
    ax.axvline(P["printed_headline"], color=ORANGE, lw=1.4)
    ax.axvspan(v["p10"], v["p90"], color=BLUE, alpha=0.12, linewidth=0)
    ax.set_title(
        titles[k] + f"\nmedian \\${v['median']:.0f}B, 80% range \\${v['p10']:.0f}B to \\${v['p90']:.0f}B",
        fontsize=8,
        loc="left",
        color=INK,
    )
    ax.set_xlabel("Headline (AUD billions)")
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
from matplotlib.lines import Line2D  # noqa: E402

fig.legend(
    handles=[Line2D([0], [0], color=ORANGE, lw=1.6, label="Reported headline, \\$159B")],
    loc="lower right",
    frameon=False,
    fontsize=7.5,
    bbox_to_anchor=(0.99, 0.0),
)
fig.tight_layout(rect=[0, 0.05, 1, 1])
fig.savefig(OUT_F / "fig4_monte_carlo.png", dpi=220)
plt.close(fig)

# ---------------------------------------------------------------- 5. Break-even hours
def m3_at_hours(h):
    return compute(P, os_hours=h)["m3"]


lo, hi = 0.0, 87.0
for _ in range(80):
    mid = (lo + hi) / 2
    if m3_at_hours(mid) > P["printed_m3"]:
        hi = mid
    else:
        lo = mid
KEY["hours_for_m3_equals_printed_130"] = (lo + hi) / 2

# ---------------------------------------------------------------- 6. Regression uncertainty
nd = NormalDist()
coef, p_val = P["reg_coef"], P["reg_p"]
z = nd.inv_cdf(1 - p_val / 2)
se = abs(coef) / z
ci95 = (coef - 1.96 * se, coef + 1.96 * se)
ci90 = (coef - 1.645 * se, coef + 1.645 * se)
scale = P["reg_foregone"] / coef  # AUD bn per unit of coefficient
KEY["regression"] = {
    "coef": coef,
    "p": p_val,
    "implied_se": se,
    "ci95_coef": ci95,
    "ci90_coef": ci90,
    "effect_per_0p1pp_pct": coef * 0.001 * 100,
    "foregone_point_bn": P["reg_foregone"],
    "foregone_ci95_bn": tuple(sorted((ci95[0] * scale, ci95[1] * scale))),  # negative = investment gain
    "note": "Normal approximation backed out from the printed p-value; assumes the model is linear in the share of compliance workers.",
}

# ---------------------------------------------------------------- 7. Error-cost threshold (theory only)
ratio = np.logspace(-1, 2, 300)  # cost of a miss relative to cost of a false flag
threshold = 1 / (1 + ratio)  # flag if P(obligation | evidence) >= c_fp / (c_fp + c_fn)
fig, ax = plt.subplots(figsize=(6.0, 2.7))
ax.plot(ratio, threshold, color=BLUE, lw=2)
ax.set_xscale("log")
for r_ in (0.2, 1, 5):
    ax.plot([r_], [1 / (1 + r_)], "o", color=ORANGE, ms=6, mec="white", mew=1.5)
    ax.annotate(
        f"{1 / (1 + r_):.2f}",
        (r_, 1 / (1 + r_)),
        textcoords="offset points",
        xytext=(7, 6),
        fontsize=8,
        color=INK,
    )
ax.set_xlabel("Cost of a missed obligation divided by cost of a false flag (log scale)")
ax.set_ylabel("Evidence needed to flag")
ax.grid(color=GRID, lw=0.6)
ax.set_axisbelow(True)
ax.set_ylim(0, 1)
put_title(fig, "Flag only when the evidence passes cost(false flag) / (cost(false flag) + cost(miss))")
fig.savefig(OUT_F / "fig5_error_cost_threshold.png", dpi=220)
plt.close(fig)

# ---------------------------------------------------------------- 8. Reconciliation figure
fig, ax = plt.subplots(figsize=(6.6, 2.4))
labels = list(meth.method)[::-1]
pv = list(meth.printed_bn)[::-1]
rv = list(meth.recomputed_bn)[::-1]
for i, (a, b_) in enumerate(zip(pv, rv)):
    ax.plot([a, b_], [i, i], color=GRID, lw=3, solid_capstyle="round", zorder=1)
    ax.plot([a], [i], "o", color=ORANGE, ms=7, zorder=2, mec="white", mew=1.5)
    ax.plot([b_], [i], "o", color=BLUE, ms=7, zorder=2, mec="white", mew=1.5)
    ax.text(max(a, b_) + 3, i, f"\\${a:.0f}B printed, \\${b_:.0f}B recomputed", va="center", fontsize=7.5, color=INK)
ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels, fontsize=8)
ax.plot([], [], "o", color=ORANGE, label="Printed in the report")
ax.plot([], [], "o", color=BLUE, label="Recomputed from printed inputs")
ax.legend(loc="upper left", frameon=False, fontsize=7.5)
ax.set_xlim(100, 270)
ax.set_xlabel("AUD billions")
ax.grid(axis="x", color=GRID, lw=0.6)
ax.set_axisbelow(True)
put_title(fig, "Printed figures against the same formulas run on the printed inputs", top=0.9)
fig.savefig(OUT_F / "fig1_reconciliation.png", dpi=220)
plt.close(fig)

# ---------------------------------------------------------------- 9. 25% cut in dollars
KEY["cut25"] = {
    "at_reported_160": 0.25 * 160,
    "at_m3_printed_130": 0.25 * 130,
    "at_m1_printed_190": 0.25 * 190,
}

with open(ROOT / "outputs" / "key_numbers.json", "w") as f:
    json.dump(KEY, f, indent=2, default=float)

print(json.dumps(KEY, indent=2, default=float)[:6000])
