"""
suggestTarget.py  —  Prospective mode
--------------------------------------
Gợi ý KPI range dựa trên thông tin CÓ SẴN tại thời điểm đặt target.

  2014 : Không có prior year data.
         3 tháng đầu là giai đoạn thử nghiệm → không đặt target.
         Sau Q1 (tháng 4): dùng actual Jan-Mar + XGBoost seasonal weights
         để project annual → tính tier ranges.
         baseline_2014 = sum(actual[Jan-Mar]) / sum(w_xgb[Jan-Mar])

  2015 : baseline = ANNUAL_TARGET_2015 từ monthlyForecast2014
         (predict được sinh ra cuối năm 2014)

  2016 : baseline = ANNUAL_TARGET_2016 từ monthlyForecast2015

  2017 : baseline = ANNUAL_TARGET_2017 từ monthlyForecast2016

  2018 : baseline = ANNUAL_TARGET_2018 từ monthlyForecast2017

Tier multipliers:
  Achievable  1.10x  — cần thêm 10% nỗ lực, khả thi
  Challenging 1.20x  — cần push mạnh, cần kế hoạch rõ ràng
  Stretch     1.35x  — xuất sắc, cần đột phá
  Moonshot    1.50x  — tham vọng tối đa, rủi ro cao

Lưu vào target/:
  suggestTargetResult.md
  suggestTargetConst.py
  suggestTargetChart.png
"""

import os
import sys

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
TARGET_DIR = os.path.join(BASE_DIR, 'target')
os.makedirs(TARGET_DIR, exist_ok=True)
sys.path.insert(0, BASE_DIR)

print("Loading forecast chain 2014 -> 2017 ...")

from monthlyForecast2014 import (
    ACTUAL_2014,
    ANNUAL_TARGET_2015 as BASELINE_2015,
    w_prior            as W_PRIOR_2014,   # XGBoost weights trước khi thấy actual 2014
)
from monthlyForecast2015 import (
    ACTUAL_2015,
    ANNUAL_TARGET_2016 as BASELINE_2016,
)
from monthlyForecast2016 import (
    ACTUAL_2016,
    ANNUAL_TARGET_2017 as BASELINE_2017,
)
from monthlyForecast2017 import (
    ACTUAL_2017,
    ANNUAL_TARGET_2018 as BASELINE_2018,
)

print("Done.\n")

# ── Constants ─────────────────────────────────────────────────────────────────
METRICS = ['Sales', 'Profit', 'Customers', 'Orders']
UNIT    = {'Sales': '$', 'Profit': '$', 'Customers': '', 'Orders': ''}

TIERS = {
    'Achievable' : 1.10,
    'Challenging': 1.20,
    'Stretch'    : 1.35,
    'Moonshot'   : 1.50,
}

Q1 = [1, 2, 3]   # tháng thử nghiệm 2014

# ── 2014: project annual từ Q1 actuals + seasonal weights ─────────────────────
# Logic: sau khi có 3 tháng đầu, ta biết được nhịp thực tế.
# Dùng XGBoost seasonal weights (w_prior) để suy ra con số cả năm.
# baseline = sum_actual_Q1 / sum_weight_Q1
def project_q1(actual_dict, weights, metric):
    q1_act = sum(actual_dict[metric][m] for m in Q1)
    q1_w   = sum(float(weights[metric][m - 1]) for m in Q1)
    return round(q1_act / q1_w, 2) if q1_w > 0 else 0.0

BASELINE_2014 = {metric: project_q1(ACTUAL_2014, W_PRIOR_2014, metric)
                 for metric in METRICS}

# ── Baselines per year ────────────────────────────────────────────────────────
BASELINES = {
    2014: BASELINE_2014,                                      # Q1-projection
    2015: {m: float(BASELINE_2015[m]) for m in METRICS},     # end-of-2014 predict
    2016: {m: float(BASELINE_2016[m]) for m in METRICS},     # end-of-2015 predict
    2017: {m: float(BASELINE_2017[m]) for m in METRICS},     # end-of-2016 predict
    2018: {m: float(BASELINE_2018[m]) for m in METRICS},     # end-of-2017 predict
}

# ── Actuals (for comparison) ──────────────────────────────────────────────────
ACTUALS = {
    2014: {m: sum(ACTUAL_2014[m].values()) for m in METRICS},
    2015: {m: sum(ACTUAL_2015[m].values()) for m in METRICS},
    2016: {m: sum(ACTUAL_2016[m].values()) for m in METRICS},
    2017: {m: sum(ACTUAL_2017[m].values()) for m in METRICS},
}

# ── Q1 actuals detail (for 2014 explanation) ──────────────────────────────────
Q1_ACTUALS = {
    metric: {m: ACTUAL_2014[metric][m] for m in Q1}
    for metric in METRICS
}
Q1_WEIGHTS = {
    metric: {m: float(W_PRIOR_2014[metric][m - 1]) for m in Q1}
    for metric in METRICS
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def tier_range(baseline):
    return {t: round(baseline * mult) for t, mult in TIERS.items()}

def classify(actual, baseline):
    if not baseline: return '?'
    r = actual / baseline
    if r < 0.95:    return 'Below baseline'
    if r < 1.05:    return 'Baseline'
    if r < 1.15:    return 'Achievable'
    if r < 1.275:   return 'Challenging'
    if r < 1.425:   return 'Stretch'
    return 'Moonshot'

def fmt(v, unit, w=12):
    if v is None: return ' ' * w
    return f"${v:>{w-1},.0f}" if unit == '$' else f"{v:>{w},.0f}"

def pct(v, ref):
    if not ref: return '    -- '
    return f"{(v/ref - 1)*100:>+6.1f}%"

# ── SUGGESTED_RANGES: exportable ─────────────────────────────────────────────
SUGGESTED_RANGES = {
    year: {metric: tier_range(BASELINES[year][metric]) for metric in METRICS}
    for year in [2014, 2015, 2016, 2017, 2018]
}

TIER_ICON = {        # for MD only
    'Moonshot'      : '🚀',
    'Stretch'       : '💪',
    'Challenging'   : '🎯',
    'Achievable'    : '✅',
    'Baseline'      : '~',
    'Below baseline': '!!',
}
TIER_TEXT = {       # for terminal (ASCII-safe)
    'Moonshot'      : '[MOONSHOT]',
    'Stretch'       : '[STRETCH]',
    'Challenging'   : '[CHALLENGING]',
    'Achievable'    : '[ACHIEVABLE]',
    'Baseline'      : '[BASELINE]',
    'Below baseline': '[BELOW BASELINE]',
}

# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    W = 96

    # ── 2014 Q1 projection detail ─────────────────────────────────────────────
    print('=' * W)
    print(f"{'2014  Q1 PROJECTION  (basis for 2014 target — set after month 3)':^{W}}")
    print('=' * W)
    print(f"  {'Metric':<12}  {'Jan actual':>12}  {'Feb actual':>12}  "
          f"{'Mar actual':>12}  {'Q1 total':>12}  {'Q1 weight':>10}  {'Projected annual':>17}")
    print('  ' + '-' * 82)
    for metric in METRICS:
        u    = UNIT[metric]
        q1a  = Q1_ACTUALS[metric]
        q1w  = Q1_WEIGHTS[metric]
        tot  = sum(q1a.values())
        wtot = sum(q1w.values())
        proj = BASELINE_2014[metric]
        print(f"  {metric:<12}  {fmt(q1a[1],u)}  {fmt(q1a[2],u)}  "
              f"{fmt(q1a[3],u)}  {fmt(tot,u)}  {wtot:>9.2%}  {fmt(proj,u,17)}")
    print()

    # ── Tier ranges per year ──────────────────────────────────────────────────
    for metric in METRICS:
        u = UNIT[metric]
        print('=' * W)
        print(f"  {metric.upper()}  —  KPI RANGE SUGGESTION  (Prospective)")
        print(f"  Baseline source: 2014=Q1-projection | 2015-2017=prev-year predict | 2018=2017-predict")
        print('=' * W)
        print(f"  {'Year':<6}  {'Baseline':>12}  {'Achievable':>12}  "
              f"{'Challenging':>12}  {'Stretch':>12}  {'Actual':>12}  {'Tier'}")
        print('  ' + '-' * 82)
        for year in [2014, 2015, 2016, 2017, 2018]:
            base   = BASELINES[year][metric]
            r      = tier_range(base)
            actual = ACTUALS.get(year, {}).get(metric)
            tier   = classify(actual, base) if actual else '(no data)'
            ttxt   = TIER_TEXT.get(tier, tier)
            a_str  = fmt(actual, u) if actual else f"{'--':>12}"
            note   = ' <- set after Q1' if year == 2014 else ''
            print(f"  {year:<6}  {fmt(base,u)}  {fmt(r['Achievable'],u)}  "
                  f"{fmt(r['Challenging'],u)}  {fmt(r['Stretch'],u)}  "
                  f"{a_str}  {ttxt}{note}")
        print()

    # ── Year-on-year summary ──────────────────────────────────────────────────
    print('=' * W)
    print(f"{'ACTUAL PERFORMANCE vs BASELINE  (prospective baseline)':^{W}}")
    print('=' * W)
    print(f"  {'Metric':<12}  {'Year'}  {'Baseline':>14}  {'Actual':>14}  "
          f"{'vs Baseline':>12}  Tier")
    print('  ' + '-' * 72)
    for metric in METRICS:
        u = UNIT[metric]
        for year in [2014, 2015, 2016, 2017]:
            base = BASELINES[year][metric]
            act  = ACTUALS[year][metric]
            tier = classify(act, base)
            ttxt = TIER_TEXT.get(tier, tier)
            print(f"  {metric:<12}  {year}  {fmt(base,u,14)}  "
                  f"{fmt(act,u,14)}  {pct(act,base):>12}  {ttxt}")
        print()

    # ── 2018 recommendation ───────────────────────────────────────────────────
    print('=' * W)
    print(f"{'2018  KPI RECOMMENDATION':^{W}}")
    print(f"{'Baseline from monthlyForecast2017 end-of-year predict':^{W}}")
    print('=' * W)
    print(f"  {'Metric':<12}  {'Baseline':>12}  {'Achievable (+10%)':>18}  "
          f"{'Challenging (+20%)':>19}  {'Stretch (+35%)':>15}")
    print('  ' + '-' * 72)
    for metric in METRICS:
        u = UNIT[metric]
        r = SUGGESTED_RANGES[2018][metric]
        print(f"  {metric:<12}  {fmt(BASELINES[2018][metric],u)}  "
                  f"{fmt(r['Achievable'],u):>18}  "
                  f"{fmt(r['Challenging'],u):>19}  "
                  f"{fmt(r['Stretch'],u):>15}")
    print()

    # ─────────────────────────────────────────────────────────────────────────
    #  SAVE
    # ─────────────────────────────────────────────────────────────────────────
    def mfmt(v, u):
        if v is None: return '--'
        return f"${v:,.0f}" if u == '$' else f"{int(v):,}"

    # ── MD ────────────────────────────────────────────────────────────────────
    md_path = os.path.join(TARGET_DIR, 'suggestTargetResult.md')
    L = []
    L.append('# KPI Suggest Target — Prospective Mode\n')
    L.append('> **Logic:** 2014 = Q1 projection | 2015–2017 = predict từ năm trước | 2018 = projection\n')

    L.append('## 2014 — Q1 Projection Detail\n')
    L.append('> Target 2014 được đặt **sau Q1** (tháng 4). 3 tháng đầu là giai đoạn thử nghiệm.\n')
    L.append('| Metric | Jan | Feb | Mar | Q1 Total | Q1 Weight | Projected Annual |')
    L.append('|--------|----:|----:|----:|---------:|----------:|-----------------:|')
    for metric in METRICS:
        u   = UNIT[metric]
        q1a = Q1_ACTUALS[metric]
        q1w = Q1_WEIGHTS[metric]
        tot = sum(q1a.values())
        wtot= sum(q1w.values())
        proj= BASELINE_2014[metric]
        L.append(f'| **{metric}** | {mfmt(q1a[1],u)} | {mfmt(q1a[2],u)} | '
                 f'{mfmt(q1a[3],u)} | **{mfmt(tot,u)}** | {wtot:.2%} | **{mfmt(proj,u)}** |')
    L.append('')

    L.append('## KPI Range by Year\n')
    for metric in METRICS:
        u = UNIT[metric]
        L.append(f'### {metric}\n')
        L.append('| Year | Baseline | Achievable | Challenging | Stretch | Actual | Tier |')
        L.append('|------|----------|------------|-------------|---------|--------|------|')
        for year in [2014, 2015, 2016, 2017, 2018]:
            base   = BASELINES[year][metric]
            r      = tier_range(base)
            actual = ACTUALS.get(year, {}).get(metric)
            tier   = classify(actual, base) if actual else '—'
            icon   = TIER_ICON.get(tier, '')
            src    = ' *(Q1 proj)*' if year == 2014 else ''
            L.append(f'| {year}{src} | {mfmt(base,u)} | **{mfmt(r["Achievable"],u)}** | '
                     f'**{mfmt(r["Challenging"],u)}** | {mfmt(r["Stretch"],u)} | '
                     f'{mfmt(actual,u) if actual else "--"} | {icon} {tier} |')
        L.append('')

    L.append('## 2018 Recommendation\n')
    L.append('| Metric | Baseline | Achievable (+10%) | Challenging (+20%) | Stretch (+35%) |')
    L.append('|--------|----------|-------------------|--------------------|----------------|')
    for metric in METRICS:
        u = UNIT[metric]; r = SUGGESTED_RANGES[2018][metric]
        L.append(f'| **{metric}** | {mfmt(BASELINES[2018][metric],u)} | '
                 f'**{mfmt(r["Achievable"],u)}** | **{mfmt(r["Challenging"],u)}** | '
                 f'{mfmt(r["Stretch"],u)} |')

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
    print(f"Saved: {md_path}")

    # ── Constants ─────────────────────────────────────────────────────────────
    py_path = os.path.join(TARGET_DIR, 'suggestTargetConst.py')
    with open(py_path, 'w', encoding='utf-8') as f:
        f.write('# Auto-generated by suggestTarget.py (Prospective)\n\n')
        f.write('TIERS      = ' + repr(TIERS)            + '\n\n')
        f.write('BASELINES  = ' + repr(BASELINES)        + '\n\n')
        f.write('ACTUALS    = ' + repr(ACTUALS)           + '\n\n')
        f.write('SUGGESTED_RANGES = ' + repr(SUGGESTED_RANGES) + '\n\n')
        f.write('Q1_ACTUALS = ' + repr(Q1_ACTUALS)       + '\n\n')
        f.write('Q1_WEIGHTS = ' + repr(Q1_WEIGHTS)       + '\n')
    print(f"Saved: {py_path}")

    # ── Chart ─────────────────────────────────────────────────────────────────
    try:
        import matplotlib; matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np

        TC = {'Achievable':'#1f77b4','Challenging':'#2ca02c',
              'Stretch':'#ff7f0e','Moonshot':'#d62728'}
        YA = [2014,2015,2016,2017]; YL = [2014,2015,2016,2017,2018]
        LABELS = {2014:'2014\n(Q1 proj)',2015:'2015',2016:'2016',
                  2017:'2017',2018:'2018\n(proj)'}

        def bar_color(a, b):
            t = classify(a, b)
            return {'Below baseline':'#cc3333','Baseline':'#aec7e8',
                    'Achievable':'#1f77b4','Challenging':'#2ca02c',
                    'Stretch':'#ff7f0e','Moonshot':'#d62728'}.get(t,'#888')

        fig, axes = plt.subplots(2, 2, figsize=(14, 9))
        fig.suptitle('KPI Suggested Ranges — Prospective  (2014–2018)',
                     fontsize=13, fontweight='bold')

        for ax, metric in zip(axes.flat, METRICS):
            u = UNIT[metric]
            x = np.arange(len(YL))
            prev = [BASELINES[y][metric] for y in YL]
            for t, c in TC.items():
                curr = [BASELINES[y][metric] * TIERS[t] for y in YL]
                ax.fill_between(x, prev, curr, alpha=0.18, color=c)
                prev = curr
            ax.plot(x, [BASELINES[y][metric] for y in YL],
                    'k--', lw=1.1, alpha=0.45, label='Baseline')
            av = [ACTUALS[y][metric] for y in YA]
            bc = [bar_color(a, BASELINES[y][metric]) for a, y in zip(av, YA)]
            ax.bar(x[:4], av, color=bc, alpha=0.82, width=0.5, zorder=3)
            for xi, v in zip(x[:4], av):
                lbl = f'${v/1000:.0f}K' if u=='$' else f'{int(v):,}'
                ax.text(xi, v*1.03, lbl, ha='center', va='bottom',
                        fontsize=7.5, fontweight='bold')
            r18 = SUGGESTED_RANGES[2018][metric]
            ax.scatter([x[4]], [r18['Achievable']], marker='D', s=90,
                       color='#1f77b4', zorder=5)
            ax.scatter([x[4]], [r18['Challenging']], marker='D', s=90,
                       color='#2ca02c', zorder=5)
            ax.set_title(metric, fontsize=11, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels([LABELS[y] for y in YL], fontsize=8)
            if u == '$':
                ax.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda v, _: f'${v/1000:.0f}K'))
            else:
                ax.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda v, _: f'{int(v):,}'))
            ax.grid(axis='y', alpha=0.25)
            ax.set_xlim(-0.6, 4.6)
            # Mark 2014 x-label differently
            ax.get_xticklabels()[0].set_color('#cc5500')
            ax.get_xticklabels()[0].set_fontweight('bold')

        patches = [mpatches.Patch(color='#aec7e8', alpha=0.6, label='Baseline')]
        patches += [mpatches.Patch(color=c, alpha=0.4, label=t)
                    for t, c in TC.items()]
        patches += [
            plt.Line2D([0],[0], marker='D', color='#1f77b4', ls='', ms=7,
                       label='2018 Achievable'),
            plt.Line2D([0],[0], marker='D', color='#2ca02c', ls='', ms=7,
                       label='2018 Challenging'),
        ]
        fig.legend(handles=patches, loc='lower center', ncol=7,
                   fontsize=8, bbox_to_anchor=(0.5, 0.0))
        plt.tight_layout(rect=[0, 0.06, 1, 0.97])
        png_path = os.path.join(TARGET_DIR, 'suggestTargetChart.png')
        plt.savefig(png_path, dpi=110, bbox_inches='tight')
        plt.close()
        print(f"Saved: {png_path}")

    except ImportError:
        print("matplotlib not found — skip chart.")
