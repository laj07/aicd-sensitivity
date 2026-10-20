"""
Replication of the three-method estimate in
"$160 billion and counting: The cost of Commonwealth regulatory complexity"
(Mandala for the AICD, Nov 2025).

Every number comes from data/inputs.csv, which records the printed page for each input.
Nothing here is the author's own estimate of the true cost; it re-runs the report's arithmetic
so that the effect of each assumption can be isolated.

Units: AUD billions unless stated.
"""
from __future__ import annotations

import csv
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
INPUTS_CSV = ROOT / "data" / "inputs.csv"

CX_KEYS = [
    "cx_notional",
    "cx_structural",
    "cx_penalty",
    "cx_defined",
    "cx_instruments",
    "cx_interconnect",
]


def load_inputs(path: Path = INPUTS_CSV) -> dict[str, float]:
    out: dict[str, float] = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            out[row["id"]] = float(row["value"])
    return out


def derived_drivers(p: dict[str, float]) -> dict[str, float]:
    """Drivers that the report states as a single number but which are built from inputs."""
    return {
        "base_proj": p["gdp_share_2013"] * p["gdp_2024"],  # printed as $113B
        "vol_mult": p["pages_2024"] / p["pages_2013"],  # printed as +24%
        "cx_mult": 1 + mean(p[k] for k in CX_KEYS),  # printed as +35%
        "cpi_mult": 1 + p["cpi_2013_24"],  # printed as +35%
        "role_mult": p["roles_2024"] / p["roles_2013"],  # printed as +74%
    }


def compute(inputs: dict[str, float] | None = None, **overrides: float) -> dict[str, float]:
    """
    Run the three methods.

    `overrides` may replace any raw input (e.g. os_hours=60) or any derived driver
    (base_proj, vol_mult, cx_mult, cpi_mult, role_mult). The special key `os_oh_mult`
    sets a separate overhead multiplier for 'other staff' time (default: same as oh_mult).
    """
    p = dict(inputs if inputs is not None else load_inputs())
    ov = dict(overrides)
    d = derived_drivers(p)
    # raw-input overrides first (so derived drivers see them), then driver overrides
    for k in list(ov):
        if k in p:
            p[k] = ov.pop(k)
    d = derived_drivers(p)
    for k in list(ov):
        if k in d:
            d[k] = ov.pop(k)
    os_oh_mult = ov.pop("os_oh_mult", p["oh_mult"])
    if ov:
        raise KeyError(f"unknown override(s): {sorted(ov)}")

    oh = p["oh_mult"] - 1.0
    os_oh = os_oh_mult - 1.0

    # Method 1: volume and complexity
    m1 = d["base_proj"] * d["vol_mult"] * d["cx_mult"]
    # Method 2: inflation and compliance roles
    m2 = p["base_2013"] * d["cpi_mult"] * d["role_mult"]
    # Method 3: bottom-up
    items = {}
    items["cw_labour"] = p["cw_workers"] * p["fte"] * p["cw_salary"] / 1e9
    items["cw_overhead"] = items["cw_labour"] * oh
    items["internal_legal"] = p["il_workers"] * p["fte"] * p["il_salary"] * p["il_share"] / 1e9
    items["internal_audit"] = p["ia_workers"] * p["fte"] * p["ia_salary"] * p["ia_share"] / 1e9
    items["legal_audit_overhead"] = (items["internal_legal"] + items["internal_audit"]) * oh
    items["other_staff_labour"] = (p["os_hours"] * p["os_workers"] - p["os_excl"]) * p["os_wage"] / 1e9
    items["other_staff_overhead"] = items["other_staff_labour"] * os_oh
    items["it_systems"] = p["it_spend"] * p["it_share"]
    items["external_legal"] = p["el_workers"] * p["fte"] * p["el_rev"] * p["el_share"] / 1e9
    items["external_audit"] = p["ea_fees"] / p["ea_div"] * p["ea_share"]
    total_all_levels = sum(items.values())
    state = p["state_share_gsp"] * p["gsp_total"]
    m3 = total_all_levels - state

    out = {
        "m1": m1,
        "m2": m2,
        "m3": m3,
        "headline": (m1 + m2 + m3) / 3,
        "m3_total_all_levels": total_all_levels,
        "m3_state": state,
        **{f"item_{k}": v for k, v in items.items()},
        **{f"drv_{k}": v for k, v in d.items()},
    }
    out["other_staff_share_of_m3_total"] = (
        items["other_staff_labour"] + items["other_staff_overhead"]
    ) / total_all_levels
    return out


# What the report prints, for side-by-side comparison
PRINTED_ITEMS = {
    "cw_labour": 6.0,
    "cw_overhead": 4.0,
    "internal_legal": 1.0,
    "internal_audit": 1.0,
    "legal_audit_overhead": 1.5,
    "other_staff_labour": 58.0,
    "other_staff_overhead": 44.0,
    "it_systems": 41.0,
    "external_legal": 4.0,
    "external_audit": 0.4,
}


def printed_reference(p: dict[str, float] | None = None) -> dict[str, float]:
    p = p or load_inputs()
    items_sum = sum(PRINTED_ITEMS.values())
    return {
        "m1": p["printed_m1"],
        "m2": p["printed_m2"],
        "m3": p["printed_m3"],
        "headline_avg_of_printed": (p["printed_m1"] + p["printed_m2"] + p["printed_m3"]) / 3,
        "headline_printed": p["printed_headline"],
        "items_sum": items_sum,
        "items_sum_less_state": items_sum - p["state_share_gsp"] * p["gsp_total"],
    }


if __name__ == "__main__":
    r = compute()
    pr = printed_reference()
    print("Recomputed from printed inputs (unrounded):")
    for k in ("m1", "m2", "m3", "headline"):
        print(f"  {k:9s} {r[k]:8.1f}")
    print("Printed by the report:")
    for k, v in pr.items():
        print(f"  {k:24s} {v:8.1f}")
