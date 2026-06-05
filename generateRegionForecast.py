"""
generateRegionForecast.py
--------------------------
Import region forecast data from all 4 year modules and write
expectKPIsOutput/preditTargetRegion.md
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(BASE_DIR, 'expectKPIsOutput', 'preditTargetRegion.md')
sys.path.insert(0, BASE_DIR)

from monthlyForecast2014 import (
    ACTUAL_2014_REGION, FORECAST_2014_REGION,
    ANNUAL_TARGET_2014_REGION, REGION_SHARE_2014,
    METRICS, REGIONS, UNIT, MA,
)
from monthlyForecast2015 import (
    ACTUAL_2015_REGION, FORECAST_2015_REGION,
    ANNUAL_TARGET_2015_REGION, REGION_SHARE_2015,
)
from monthlyForecast2016 import (
    ACTUAL_2016_REGION, FORECAST_2016_REGION,
    ANNUAL_TARGET_2016_REGION, REGION_SHARE_2016,
)
from monthlyForecast2017 import (
    ACTUAL_2017_REGION, FORECAST_2017_REGION,
    ANNUAL_TARGET_2017_REGION,
)

YEARS = [2014, 2015, 2016, 2017]
ACTUALS_REGION = {
    2014: ACTUAL_2014_REGION,
    2015: ACTUAL_2015_REGION,
    2016: ACTUAL_2016_REGION,
    2017: ACTUAL_2017_REGION,
}
FORECASTS_REGION = {
    2014: FORECAST_2014_REGION,
    2015: FORECAST_2015_REGION,
    2016: FORECAST_2016_REGION,
    2017: FORECAST_2017_REGION,
}
ANNUAL_TARGETS_REGION = {
    2014: ANNUAL_TARGET_2014_REGION,
    2015: ANNUAL_TARGET_2015_REGION,
    2016: ANNUAL_TARGET_2016_REGION,
    2017: ANNUAL_TARGET_2017_REGION,
}
REGION_SHARES = {
    2014: REGION_SHARE_2014,
    2015: REGION_SHARE_2015,
    2016: REGION_SHARE_2016,
    2017: {r: {m: 0.0 for m in METRICS} for r in REGIONS},  # 2017 share not exported
}

# ── Format helpers ────────────────────────────────────────────────────────────
def fmt_val(value, metric):
    u = UNIT[metric]
    if u == '$':
        return f"${value:,.0f}"
    return f"{value:,.0f}"

def fmt_pct(value):
    sign = '+' if value >= 0 else ''
    return f"{sign}{value:.1f}%"

# ── Build markdown ─────────────────────────────────────────────────────────────
lines = []

lines.append("# Region-Level Monthly Forecast — 2014–2017")
lines.append("")
lines.append("> **Model:** XGBoost Seasonal Weights + Adaptive Annual Estimate  ")
lines.append("> **Region share basis:** prior-year actual distribution  ")
lines.append("> **Hyperparameters:** alpha = 0.30 | beta = 0.50 | base_growth = 10%")
lines.append("")
lines.append("---")
lines.append("")

for year in YEARS:
    actuals  = ACTUALS_REGION[year]
    forecasts = FORECASTS_REGION[year]
    targets  = ANNUAL_TARGETS_REGION[year]

    lines.append(f"## {year}")
    lines.append("")

    share_note = {
        2014: "2014 actual share (retrospective — first year, no prior available)",
        2015: "2014 actual share",
        2016: "2015 actual share",
        2017: "2016 actual share",
    }
    lines.append(f"> Region share basis: {share_note[year]}")
    lines.append("")

    for metric in METRICS:
        u = UNIT[metric]
        lines.append(f"### {metric}")
        lines.append("")

        # ── Annual summary table ──────────────────────────────────────────────
        lines.append("**Annual summary**")
        lines.append("")
        lines.append("| Region | Ann. Target | Actual | Gap% |")
        lines.append("|--------|------------:|-------:|-----:|")
        for region in REGIONS:
            ann_r = targets[region][metric]
            act_r = sum(actuals[region][metric].values())
            gap_r = round((act_r - ann_r) / ann_r * 100, 1) if ann_r else 0.0
            lines.append(
                f"| {region} | {fmt_val(ann_r, metric)} | {fmt_val(act_r, metric)} | {fmt_pct(gap_r)} |"
            )
        lines.append("")

        # ── Monthly detail per region ─────────────────────────────────────────
        for region in REGIONS:
            lines.append(f"#### {region}")
            lines.append("")
            lines.append(f"| Month | Target | Actual | Error% | Annual Est. |")
            lines.append(f"|-------|-------:|-------:|-------:|------------:|")
            for m in range(1, 13):
                r       = forecasts[region][metric][m]
                t, a, e = r['target'], r['actual'], r['error_pct']
                ae      = r['annual_est']
                lines.append(
                    f"| {MA[m]} | {fmt_val(t, metric)} | {fmt_val(a, metric)} "
                    f"| {fmt_pct(e)} | {fmt_val(ae, metric)} |"
                )
            act_total  = sum(actuals[region][metric].values())
            tgt_total  = sum(forecasts[region][metric][m]['target'] for m in range(1, 13))
            lines.append(f"| **Total** | **{fmt_val(tgt_total, metric)}** | **{fmt_val(act_total, metric)}** | — | — |")
            lines.append("")

        lines.append("---")
        lines.append("")

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(lines))

print(f"Saved -> {OUT_PATH}")
