"""
Builds excel/aicd_cost_model.xlsx with live formulas (no pasted results).

Run from the repo root:  python excel/build_excel.py
Every input lives on the 'Inputs' sheet (blue font) with the report page it came from.
Every other number is a formula that traces back to those inputs.
"""
from __future__ import annotations

import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "excel" / "aicd_cost_model.xlsx"

BLUE_FONT = Font(color="1F4FBF")
BOLD = Font(bold=True)
HDR_FILL = PatternFill("solid", fgColor="E8EEF7")
WARN_FILL = PatternFill("solid", fgColor="FFF2CC")
WRAP = Alignment(wrap_text=True, vertical="top")

wb = Workbook()

# ------------------------------------------------------------------ README
ws = wb.active
ws.title = "README"
readme = [
    ("Sensitivity model: AICD/Mandala estimate of Commonwealth compliance cost", BOLD),
    ("", None),
    (
        "Source: '$160 billion and counting: The cost of Commonwealth regulatory complexity' (Mandala for the AICD, Nov 2025). "
        "Page numbers on the Inputs sheet are the slide footers in the published PDF.",
        None,
    ),
    (
        "This workbook re-runs the report's three methods with live formulas so the effect of each assumption can be seen. "
        "It is an independent analysis of published figures. It is not Mandala's or the AICD's model and is not an estimate of the true cost.",
        None,
    ),
    ("", None),
    ("Sheets", BOLD),
    ("Inputs: every number taken from the report, with page and status. Blue font = input. Change a value and everything updates.", None),
    ("Model: the three methods and the headline, next to what the report prints.", None),
    ("Reconciliation: the bottom-up (Method 3) line items recomputed from their stated formulas against the printed values.", None),
    ("Scenarios: the headline under named alternative modelling choices.", None),
    ("Sensitivity: each input moved 20% down and up, with the effect on the headline.", None),
    ("Regression: what the printed p-value implies about the uncertainty around the investment result.", None),
    ("", None),
    ("Status column on Inputs", BOLD),
    ("printed = a number printed on the slide.  interpreted = printed with an evident typo corrected (see note).  assumption = not from the report; verify before relying on it.", None),
    ("", None),
    ("Cells shaded yellow need your attention (typos or unreconciled figures in the source).", None),
]
for i, (t, f) in enumerate(readme, start=1):
    c = ws.cell(row=i, column=1, value=t)
    c.alignment = WRAP
    if f:
        c.font = f
ws.column_dimensions["A"].width = 120

# ------------------------------------------------------------------ Inputs
wi = wb.create_sheet("Inputs")
hdr = ["id", "Input", "Value", "Unit", "Report page", "Status", "Note"]
for j, h in enumerate(hdr, start=1):
    c = wi.cell(row=1, column=j, value=h)
    c.font = BOLD
    c.fill = HDR_FILL
with open(ROOT / "data" / "inputs.csv", newline="") as f:
    rows = list(csv.DictReader(f))
for i, r in enumerate(rows, start=2):
    wi.cell(row=i, column=1, value=r["id"])
    wi.cell(row=i, column=2, value=r["name"])
    v = wi.cell(row=i, column=3, value=float(r["value"]))
    v.font = BLUE_FONT
    wi.cell(row=i, column=4, value=r["unit"])
    wi.cell(row=i, column=5, value=r["page"])
    st = wi.cell(row=i, column=6, value=r["status"])
    n = wi.cell(row=i, column=7, value=r["note"])
    n.alignment = WRAP
    if r["status"] in ("interpreted", "assumption"):
        for j in range(1, 8):
            wi.cell(row=i, column=j).fill = WARN_FILL
    wb.defined_names[r["id"]] = DefinedName(r["id"], attr_text=f"Inputs!$C${i}")
for col, w in zip("ABCDEFG", (22, 56, 14, 16, 12, 12, 90)):
    wi.column_dimensions[col].width = w
wi.freeze_panes = "A2"

# ------------------------------------------------------------------ Model
wm = wb.create_sheet("Model")
row = 1


def put(ws_, r, label, formula, name=None, fmt="0.0", note=None, bold=False):
    a = ws_.cell(row=r, column=1, value=label)
    b = ws_.cell(row=r, column=2, value=formula)
    b.number_format = fmt
    if bold:
        a.font = BOLD
        b.font = BOLD
    if note:
        ws_.cell(row=r, column=3, value=note).alignment = WRAP
    if name:
        wb.defined_names[name] = DefinedName(name, attr_text=f"'{ws_.title}'!$B${r}")


wm.cell(row=row, column=1, value="Derived drivers").font = BOLD
row += 1
put(wm, row, "2013 estimate projected at 4.2% of 2024 GDP (AUD bn)", "=gdp_share_2013*gdp_2024", "d_base_proj", note="Report prints $113B (p.39)")
row += 1
put(wm, row, "Volume multiplier (pages 2024 / pages 2013)", "=pages_2024/pages_2013", "d_vol_mult", "0.000", "Report prints +24% (p.39)")
row += 1
put(wm, row, "Complexity multiplier (1 + mean of six metrics)", "=1+AVERAGE(cx_notional,cx_structural,cx_penalty,cx_defined,cx_instruments,cx_interconnect)", "d_cx_mult", "0.000", "Report prints +35% (p.39)")
row += 1
put(wm, row, "CPI multiplier", "=1+cpi_2013_24", "d_cpi_mult", "0.000", "Report prints +35% (p.39)")
row += 1
put(wm, row, "Compliance-role multiplier (roles 2024 / roles 2013)", "=roles_2024/roles_2013", "d_role_mult", "0.000", "Report prints +74% (p.39); 52/30 is +73.3%")
row += 2

wm.cell(row=row, column=1, value="Method 1: volume and complexity").font = BOLD
row += 1
put(wm, row, "Method 1 (AUD bn)", "=d_base_proj*d_vol_mult*d_cx_mult", "m1", bold=True, note="Report prints ~$190B (p.39)")
row += 2
wm.cell(row=row, column=1, value="Method 2: inflation and compliance roles").font = BOLD
row += 1
put(wm, row, "2013 estimate adjusted for CPI (AUD bn)", "=base_2013*d_cpi_mult", None, note="Report prints $88B (p.39)")
row += 1
put(wm, row, "Method 2 (AUD bn)", "=base_2013*d_cpi_mult*d_role_mult", "m2", bold=True, note="Report prints ~$150B (p.39)")
row += 2
wm.cell(row=row, column=1, value="Method 3: bottom-up (see Reconciliation sheet for the line items)").font = BOLD
row += 1
put(wm, row, "Sum of line items, all levels of government (AUD bn)", "=Reconciliation!C13", "m3_total", note="Printed items sum to ~$161B")
row += 1
put(wm, row, "State cost of compliance (AUD bn)", "=state_share_gsp*gsp_total", "m3_state", note="Printed $27B")
row += 1
put(wm, row, "Method 3, Commonwealth (AUD bn)", "=m3_total-m3_state", "m3", bold=True, note="Report prints ~$130B (p.40)")
row += 1
put(wm, row, "Part of Method 3 that does not depend on 'other staff' or IT", "=Reconciliation!C3+Reconciliation!C4+Reconciliation!C5+Reconciliation!C6+Reconciliation!C7+Reconciliation!C11+Reconciliation!C12", "m3_fixed", note="Used by the Scenarios sheet")
row += 2
wm.cell(row=row, column=1, value="Headline").font = BOLD
row += 1
put(wm, row, "Headline = average of the three (AUD bn)", "=(m1+m2+m3)/3", "headline", bold=True, note="Report prints $159B on p.27 and ~$160B in text")
row += 1
put(wm, row, "Printed headline (AUD bn)", "=printed_headline", None)
row += 1
put(wm, row, "Average of the three printed, rounded figures (AUD bn)", "=(printed_m1+printed_m2+printed_m3)/3", "headline_printed_avg", note="Does not equal the printed $159B")
row += 1
put(wm, row, "A 25% cut at the recomputed headline (AUD bn)", "=0.25*headline", None)
row += 1
put(wm, row, "A 25% cut across the three printed methods: low / high (AUD bn)", "=0.25*printed_m3", None, note="Low: 25% of $130B")
wm.cell(row=row, column=3, value="Low: 25% of the printed $130B (Method 3)")
row += 1
put(wm, row, "", "=0.25*printed_m1", None, note="High: 25% of the printed $190B (Method 1)")
wm.column_dimensions["A"].width = 64
wm.column_dimensions["B"].width = 14
wm.column_dimensions["C"].width = 60

# ------------------------------------------------------------------ Reconciliation
wr = wb.create_sheet("Reconciliation")
for j, h in enumerate(
    ["Method 3 line item", "Formula as printed (p.40)", "Recomputed (AUD bn)", "Printed (AUD bn)", "Gap (AUD bn)", "Note"], start=1
):
    c = wr.cell(row=1, column=j, value=h)
    c.font = BOLD
    c.fill = HDR_FILL
lines = [
    ("Compliance workers labour", "52,000 x 75% FTE x $145,000", "=cw_workers*fte*cw_salary/1e9", 6, ""),
    ("Compliance workers overhead", "75% of labour (1.75 multiplier)", "=C3*(oh_mult-1)", 4, "Page 40 text says '75% of $8B'; 75% of the $5.7B salary base gives the printed $4B"),
    ("Internal legal labour", "40,000 x 75% x $141,000 x 23%", "=il_workers*fte*il_salary*il_share/1e9", 1, ""),
    ("Internal audit labour", "21,000 x 75% x $135,000 x 43%", "=ia_workers*fte*ia_salary*ia_share/1e9", 1, ""),
    ("Internal legal and audit overhead", "75% of $2B", "=(C5+C6)*(oh_mult-1)", 1.5, ""),
    ("Other staff labour", "(87 hours x 14.3M workers - 96M excluded hours) x $51/hour", "=(os_hours*os_workers-os_excl)*os_wage/1e9", 58, "p.40 states that 96,000,000 compliance, legal and audit hours are excluded; without that step the line is about $63B"),
    ("Other staff overhead", "75% of other staff labour", "=C8*(oh_mult-1)", 44, "Follows the labour line"),
    ("IT systems", "$135B x 30%", "=it_spend*it_share", 41, "$40.5B before rounding"),
    ("External legal", "63,000 x 75% x $340,000 x 23%", "=el_workers*fte*el_rev*el_share/1e9", 4, ""),
    ("External audit", "($823M / 78%) x 43%", "=ea_fees/ea_div*ea_share", 0.4, ""),
]
for i, (name, formula_txt, formula, printed, note) in enumerate(lines, start=3):
    wr.cell(row=i, column=1, value=name)
    wr.cell(row=i, column=2, value=formula_txt)
    c = wr.cell(row=i, column=3, value=formula)
    c.number_format = "0.00"
    p = wr.cell(row=i, column=4, value=printed)
    p.font = BLUE_FONT
    g = wr.cell(row=i, column=5, value=f"=C{i}-D{i}")
    g.number_format = "0.00"
    wr.cell(row=i, column=6, value=note).alignment = WRAP
    if note and "'$8B'" in note:
        for j in range(1, 7):
            wr.cell(row=i, column=j).fill = WARN_FILL
# rows 3..12 are items; row 13 total
wr.cell(row=13, column=1, value="Sum, all levels of government").font = BOLD
for col in ("C", "D", "E"):
    c = wr[f"{col}13"]
    c.value = f"=SUM({col}3:{col}12)"
    c.font = BOLD
    c.number_format = "0.0"
wr.cell(row=14, column=1, value="State cost of compliance")
wr["C14"] = "=m3_state"
wr["D14"] = 27
wr["D14"].font = BLUE_FONT
wr["E14"] = "=C14-D14"
wr.cell(row=15, column=1, value="Commonwealth (sum less state)").font = BOLD
wr["C15"] = "=C13-C14"
wr["D15"] = "=D13-D14"
wr["E15"] = "=C15-D15"
for c in ("C14", "E14", "C15", "D15", "E15"):
    wr[c].number_format = "0.0"
wr.cell(row=16, column=1, value="Report prints for Commonwealth")
wr["D16"] = "=printed_m3"
wr["F15"] = "Printed lines less state give about $134B; the report prints ~$130B (rounded)."
wr.cell(row=18, column=1, value="Share of the all-levels total that is 'other staff' time (labour + overhead)").font = BOLD
wr["C18"] = "=(C8+C9)/C13"
wr["C18"].number_format = "0%"
wr.cell(row=19, column=1, value="Hours per worker at which Method 3 would equal the printed $130B")
wr["C19"] = "=((printed_m3+m3_state-(C13-C8-C9))/(os_wage/1e9*oh_mult)+os_excl)/os_workers"
wr["C19"].number_format = "0.0"
wr["F19"] = "Linear solve: other staff labour x overhead multiplier makes up the remainder."
for col, w in zip("ABCDEF", (44, 40, 18, 18, 14, 80)):
    wr.column_dimensions[col].width = w

# ------------------------------------------------------------------ Scenarios
wsn = wb.create_sheet("Scenarios")
scen = [
    ("Report's method, recomputed", {}),
    ("Complexity: leave out notional amendments", {"cx": "=1+AVERAGE(cx_structural,cx_penalty,cx_defined,cx_instruments,cx_interconnect)"}),
    ("Complexity: median of the six metrics", {"cx": "=1+MEDIAN(cx_notional,cx_structural,cx_penalty,cx_defined,cx_instruments,cx_interconnect)"}),
    ("Complexity: no adjustment", {"cx": 1}),
    ("Compliance roles: net of employment growth", {"role": "=d_role_mult/(1+emp_growth)"}),
    ("Other-staff hours: 60", {"hours": 60}),
    ("Other-staff hours: 40", {"hours": 40}),
    ("No overhead loading on other-staff time", {"osoh": 1}),
    ("IT share of spend: 24% (report footnote)", {"it": 0.24}),
    (
        "Combined: four of the lower alternatives",
        {
            "cx": "=1+AVERAGE(cx_structural,cx_penalty,cx_defined,cx_instruments,cx_interconnect)",
            "role": "=d_role_mult/(1+emp_growth)",
            "hours": 60,
            "it": 0.24,
        },
    ),
]
wsn.cell(row=1, column=1, value="Driver / output").font = BOLD
driver_rows = [
    ("Base projected at 4.2% of GDP", "base", "=d_base_proj"),
    ("Volume multiplier", "vol", "=d_vol_mult"),
    ("Complexity multiplier", "cx", "=d_cx_mult"),
    ("CPI multiplier", "cpi", "=d_cpi_mult"),
    ("Compliance-role multiplier", "role", "=d_role_mult"),
    ("2013 baseline (AUD bn)", "b13", "=base_2013"),
    ("Hours per worker", "hours", "=os_hours"),
    ("Overhead multiplier on other-staff time", "osoh", "=oh_mult"),
    ("IT share of spend", "it", "=it_share"),
]
rmap = {}
for i, (lab, key, _) in enumerate(driver_rows, start=2):
    wsn.cell(row=i, column=1, value=lab)
    rmap[key] = i
out_start = len(driver_rows) + 3
labels_out = ["Method 1", "Method 2", "Method 3", "Headline", "Difference from printed $159B", "A 25% cut"]
for k, lab in enumerate(labels_out):
    wsn.cell(row=out_start + k, column=1, value=lab).font = BOLD
for j, (name, ov) in enumerate(scen, start=2):
    col = get_column_letter(j)
    h = wsn.cell(row=1, column=j, value=name)
    h.font = BOLD
    h.fill = HDR_FILL
    h.alignment = WRAP
    for lab, key, base_formula in driver_rows:
        val = ov.get(key, base_formula)
        c = wsn.cell(row=rmap[key], column=j, value=val)
        c.number_format = "0.000"
        if key in ov:
            c.fill = WARN_FILL
    r = lambda k: f"{col}{rmap[k]}"  # noqa: E731
    m1 = f"={r('base')}*{r('vol')}*{r('cx')}"
    m2 = f"={r('b13')}*{r('cpi')}*{r('role')}"
    m3 = f"=m3_fixed+({r('hours')}*os_workers-os_excl)*os_wage/1e9*{r('osoh')}+it_spend*{r('it')}-m3_state"
    wsn.cell(row=out_start, column=j, value=m1)
    wsn.cell(row=out_start + 1, column=j, value=m2)
    wsn.cell(row=out_start + 2, column=j, value=m3)
    wsn.cell(row=out_start + 3, column=j, value=f"=AVERAGE({col}{out_start}:{col}{out_start + 2})").font = BOLD
    wsn.cell(row=out_start + 4, column=j, value=f"={col}{out_start + 3}-printed_headline")
    wsn.cell(row=out_start + 5, column=j, value=f"=0.25*{col}{out_start + 3}")
    for k in range(6):
        wsn.cell(row=out_start + k, column=j).number_format = "0.0"
wsn.column_dimensions["A"].width = 42
for j in range(2, len(scen) + 2):
    wsn.column_dimensions[get_column_letter(j)].width = 20
wsn.row_dimensions[1].height = 48
wsn.cell(row=out_start + 7, column=1, value="Yellow cells are the choices that differ from the report's. Hours 60/40 and zero overhead on other-staff time are analyst choices; the 24% IT share is the figure in the report's own footnote.").alignment = WRAP

# ------------------------------------------------------------------ Sensitivity
wt = wb.create_sheet("Sensitivity")
params = [
    ("gdp_share_2013", "=gdp_share_2013"),
    ("base_2013", "=base_2013"),
    ("vol_mult", "=d_vol_mult"),
    ("cx_mult", "=d_cx_mult"),
    ("cpi_mult", "=d_cpi_mult"),
    ("role_mult", "=d_role_mult"),
    ("oh_mult", "=oh_mult"),
    ("os_hours", "=os_hours"),
    ("os_wage", "=os_wage"),
    ("os_workers", "=os_workers"),
    ("it_share", "=it_share"),
    ("it_spend", "=it_spend"),
    ("state_share_gsp", "=state_share_gsp"),
    ("cw_workers", "=cw_workers"),
]
cases = [
    ("2013 baseline (M1 and M2)", ["gdp_share_2013", "base_2013"]),
    ("Volume multiplier (M1)", ["vol_mult"]),
    ("Complexity multiplier (M1)", ["cx_mult"]),
    ("CPI multiplier (M2)", ["cpi_mult"]),
    ("Compliance-role multiplier (M2)", ["role_mult"]),
    ("Overhead multiplier (M3)", ["oh_mult"]),
    ("Hours per worker (M3)", ["os_hours"]),
    ("Hourly wage (M3)", ["os_wage"]),
    ("Total workers (M3)", ["os_workers"]),
    ("IT compliance share (M3)", ["it_share"]),
    ("IT spend (M3)", ["it_spend"]),
    ("State cost share (M3)", ["state_share_gsp"]),
    ("Compliance workers (M3)", ["cw_workers"]),
]
wt["A1"] = "Swing (fraction)"
wt["B1"] = 0.20
wt["B1"].font = BLUE_FONT
wt["B1"].number_format = "0%"
wb.defined_names["swing"] = DefinedName("swing", attr_text="Sensitivity!$B$1")
HEADER_ROW = 3
wt.cell(row=HEADER_ROW, column=1, value="Parameter").font = BOLD
prow = {}
for i, (key, _) in enumerate(params, start=HEADER_ROW + 1):
    wt.cell(row=i, column=1, value=key)
    prow[key] = i
o_start = HEADER_ROW + len(params) + 2
for k, lab in enumerate(["Method 1", "Method 2", "Method 3", "Headline"]):
    wt.cell(row=o_start + k, column=1, value=lab).font = BOLD
columns = [("Base", None, 0)]
for name, ps in cases:
    columns.append((name + " -20%", ps, -1))
    columns.append((name + " +20%", ps, +1))
for j, (label, ps, sign) in enumerate(columns, start=2):
    col = get_column_letter(j)
    h = wt.cell(row=HEADER_ROW, column=j, value=label)
    h.font = BOLD
    h.fill = HDR_FILL
    h.alignment = WRAP
    for key, base_formula in params:
        base = base_formula[1:]
        if ps and key in ps:
            f = f"={base}*(1{'+' if sign > 0 else '-'}swing)"
            wt.cell(row=prow[key], column=j, value=f).fill = WARN_FILL
        else:
            wt.cell(row=prow[key], column=j, value=f"={base}")
        wt.cell(row=prow[key], column=j).number_format = "#,##0.000"
    R = lambda k: f"{col}{prow[k]}"  # noqa: E731
    m1 = f"={R('gdp_share_2013')}*gdp_2024*{R('vol_mult')}*{R('cx_mult')}"
    m2 = f"={R('base_2013')}*{R('cpi_mult')}*{R('role_mult')}"
    total = (
        f"({R('cw_workers')}*fte*cw_salary/1e9"
        f"+(il_workers*fte*il_salary*il_share+ia_workers*fte*ia_salary*ia_share)/1e9"
        f"+({R('os_hours')}*{R('os_workers')}-os_excl)*{R('os_wage')}/1e9)*{R('oh_mult')}"
        f"+{R('it_spend')}*{R('it_share')}"
        f"+el_workers*fte*el_rev*el_share/1e9+ea_fees/ea_div*ea_share"
    )
    m3 = f"={total}-{R('state_share_gsp')}*gsp_total"
    wt.cell(row=o_start, column=j, value=m1)
    wt.cell(row=o_start + 1, column=j, value=m2)
    wt.cell(row=o_start + 2, column=j, value=m3)
    wt.cell(row=o_start + 3, column=j, value=f"=AVERAGE({col}{o_start}:{col}{o_start + 2})").font = BOLD
    for k in range(4):
        wt.cell(row=o_start + k, column=j).number_format = "0.0"
wt.row_dimensions[HEADER_ROW].height = 60
wt.column_dimensions["A"].width = 22
for j in range(2, len(columns) + 2):
    wt.column_dimensions[get_column_letter(j)].width = 16

# summary table
s0 = o_start + 6
for j, h in enumerate(["Driver", "Headline at -20%", "Headline at +20%", "Swing (AUD bn)", "Elasticity"], start=1):
    c = wt.cell(row=s0, column=j, value=h)
    c.font = BOLD
    c.fill = HDR_FILL
for i, (name, _) in enumerate(cases, start=s0 + 1):
    lo_col = get_column_letter(3 + 2 * (i - s0 - 1))
    hi_col = get_column_letter(4 + 2 * (i - s0 - 1))
    wt.cell(row=i, column=1, value=name)
    wt.cell(row=i, column=2, value=f"={lo_col}{o_start + 3}").number_format = "0.0"
    wt.cell(row=i, column=3, value=f"={hi_col}{o_start + 3}").number_format = "0.0"
    wt.cell(row=i, column=4, value=f"=ABS(C{i}-B{i})").number_format = "0.0"
    wt.cell(row=i, column=5, value=f"=((C{i}-B{i})/B{o_start + 3})/(2*swing)").number_format = "0.00"
last = s0 + len(cases)
ch = BarChart()
ch.type = "bar"
ch.title = "Swing in the headline from a 20% move in each input (AUD bn)"
ch.add_data(Reference(wt, min_col=4, min_row=s0, max_row=last), titles_from_data=True)
ch.set_categories(Reference(wt, min_col=1, min_row=s0 + 1, max_row=last))
ch.legend = None
ch.height = 9
ch.width = 18
wt.add_chart(ch, f"G{s0}")
wt.cell(row=last + 2, column=1, value="Elasticity = % change in the headline per 1% change in the input.")

# ------------------------------------------------------------------ Regression
wg = wb.create_sheet("Regression")
wg["A1"] = "What the printed p-value implies (p.42)"
wg["A1"].font = BOLD
reg = [
    ("Coefficient (printed)", "=reg_coef", "0.0"),
    ("p-value (printed, assumed two-sided)", "=reg_p", "0.00"),
    ("z-score implied by the p-value", "=NORMSINV(1-reg_p/2)", "0.000"),
    ("Implied standard error", "=ABS(reg_coef)/B4", "0.00"),
    ("95% interval, low", "=reg_coef-1.96*B5", "0.0"),
    ("95% interval, high", "=reg_coef+1.96*B5", "0.0"),
    ("Effect of +0.1pp on investment growth, point (%)", "=reg_coef*0.001*100", "0.00"),
    ("Effect, 95% low (%)", "=B6*0.001*100", "0.00"),
    ("Effect, 95% high (%)", "=B7*0.001*100", "0.00"),
    ("Printed foregone investment, 2025 (AUD bn)", "=reg_foregone", "0.0"),
    ("Foregone investment at the 95% low coefficient (AUD bn; positive = loss)", "=reg_foregone*B6/reg_coef", "0.0"),
    ("Foregone investment at the 95% high coefficient (AUD bn; negative = gain)", "=reg_foregone*B7/reg_coef", "0.0"),
]
for i, (lab, f, fmt) in enumerate(reg, start=2):
    wg.cell(row=i, column=1, value=lab)
    c = wg.cell(row=i, column=2, value=f)
    c.number_format = fmt
wg.cell(
    row=15,
    column=1,
    value="Assumes a normal approximation and a model that is linear in the compliance share. The 95% interval includes zero. Printed effect is 2.3%; the coefficient implies 2.24%.",
).alignment = WRAP
wg.column_dimensions["A"].width = 80
wg.column_dimensions["B"].width = 14

wb.save(OUT)
print("wrote", OUT)

# ------------------------------------------------------------------ cache values
# openpyxl writes formulas without results. Recalculate headless so previewers
# (Drive, Quick Look, phones) show numbers. Skipped if LibreOffice is missing.
import shutil
import subprocess
import tempfile

if shutil.which("soffice"):
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", tmp, str(OUT)],
            check=True,
            capture_output=True,
            timeout=180,
        )
        shutil.copy(Path(tmp) / OUT.name, OUT)
    print("recalculated and cached values")
