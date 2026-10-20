"""
Checks on the replication. Run from the repo root:  python -m pytest tests -q   (or: python tests/test_model.py)

1. Identities and monotonicity of the Python model.
2. The Python model against the Excel workbook, recalculated headless in LibreOffice
   (skipped if soffice is not installed).
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "model"))
from aicd_model import compute, load_inputs, printed_reference  # noqa: E402

P = load_inputs()
BASE = compute(P)


def close(a, b, tol=1e-6):
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def test_method_identities():
    assert close(BASE["m1"], P["gdp_share_2013"] * P["gdp_2024"] * BASE["drv_vol_mult"] * BASE["drv_cx_mult"])
    assert close(BASE["m2"], 65 * 1.35 * (52000 / 30000))
    assert close(BASE["headline"], (BASE["m1"] + BASE["m2"] + BASE["m3"]) / 3)


def test_printed_intermediate_values_reproduce():
    # The report prints $113B, +24%, +35%, $88B. These should come out of the printed inputs.
    assert abs(BASE["drv_base_proj"] - 113) < 0.5
    assert abs(BASE["drv_vol_mult"] - 1.24) < 0.01
    assert abs(BASE["drv_cx_mult"] - 1.35) < 1e-9
    assert abs(65 * BASE["drv_cpi_mult"] - 88) < 0.5


def test_methods_close_to_printed():
    pr = printed_reference(P)
    assert abs(BASE["m1"] - pr["m1"]) < 1.0  # 190
    assert abs(BASE["m2"] - pr["m2"]) < 3.0  # 150
    # Method 3 reproduces once the report's exclusion of 96 million hours is applied
    # (the printed value is "~$130B", so allow for rounding)
    assert abs(BASE["m3"] - pr["m3"]) < 5.0
    assert abs(BASE["headline"] - P["printed_headline"]) < 1.0


def test_monotonic_in_drivers():
    for key in ("os_hours", "os_wage", "it_share", "oh_mult", "cw_workers"):
        lo = compute(P, **{key: P[key] * 0.9})["headline"]
        hi = compute(P, **{key: P[key] * 1.1})["headline"]
        assert hi > lo, key
    # state share is subtracted, so the headline falls as it rises
    assert compute(P, state_share_gsp=0.02)["headline"] < BASE["headline"]


def test_unit_multipliers_collapse_method_1():
    r = compute(P, vol_mult=1.0, cx_mult=1.0)
    assert close(r["m1"], BASE["drv_base_proj"])


def test_other_staff_share():
    assert 0.6 < BASE["other_staff_share_of_m3_total"] < 0.7
    # the printed $58B only comes out once the 96M excluded hours are removed
    assert abs(BASE["item_other_staff_labour"] - 58) < 1.0


def test_unknown_override_raises():
    try:
        compute(P, not_a_key=1)
    except KeyError:
        return
    raise AssertionError("expected KeyError")


def test_excel_matches_python():
    soffice = shutil.which("soffice")
    if not soffice:
        print("soffice not found; skipping Excel cross-check")
        return
    from openpyxl import load_workbook

    src = ROOT / "excel" / "aicd_cost_model.xlsx"
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [soffice, "--headless", "--calc", "--convert-to", "xlsx", "--outdir", tmp, str(src)],
            check=True,
            capture_output=True,
            timeout=180,
        )
        wb = load_workbook(Path(tmp) / src.name, data_only=True)
    errs = [
        (ws.title, c.coordinate, c.value)
        for ws in wb
        for row in ws.iter_rows()
        for c in row
        if isinstance(c.value, str) and (c.value.startswith("#") or "Err:" in c.value)
    ]
    assert not errs, errs
    m = wb["Model"]
    labels = {m.cell(r, 1).value: m.cell(r, 2).value for r in range(1, 40)}
    assert close(labels["Method 1 (AUD bn)"], BASE["m1"])
    assert close(labels["Method 2 (AUD bn)"], BASE["m2"])
    assert close(labels["Method 3, Commonwealth (AUD bn)"], BASE["m3"])
    assert close(labels["Headline = average of the three (AUD bn)"], BASE["headline"])

    # Sensitivity: Excel swing table vs Python one-at-a-time
    t = wb["Sensitivity"]
    xl = {}
    for r in range(1, t.max_row + 1):
        if t.cell(r, 1).value == "Driver":
            r0 = r + 1
            while t.cell(r0, 2).value is not None:
                xl[t.cell(r0, 1).value] = (t.cell(r0, 2).value, t.cell(r0, 3).value)
                r0 += 1
    py_h = {
        "Hours per worker (M3)": ("os_hours", P["os_hours"]),
        "IT compliance share (M3)": ("it_share", P["it_share"]),
        "Compliance workers (M3)": ("cw_workers", P["cw_workers"]),
    }
    for name, (k, v) in py_h.items():
        lo = compute(P, **{k: v * 0.8})["headline"]
        hi = compute(P, **{k: v * 1.2})["headline"]
        assert close(xl[name][0], lo) and close(xl[name][1], hi), name

    # Scenarios: first and last columns
    s = wb["Scenarios"]
    head_row = [r for r in range(1, s.max_row + 1) if s.cell(r, 1).value == "Headline"][0]
    assert close(s.cell(head_row, 2).value, BASE["headline"])
    comb = compute(
        P,
        cx_mult=1 + sum(P[k] for k in ("cx_structural", "cx_penalty", "cx_defined", "cx_instruments", "cx_interconnect")) / 5,
        role_mult=BASE["drv_role_mult"] / (1 + P["emp_growth"]),
        os_hours=60,
        it_share=0.24,
    )["headline"]
    assert close(s.cell(head_row, 11).value, comb)


if __name__ == "__main__":
    fns = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for f in fns:
        f()
        print("ok", f.__name__)
