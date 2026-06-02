"""
monthlyTargetForecast.py
------------------------
Rolling monthly target forecast for 2015, then full forecast for 2016.

Phase 1 — Baseline (2014):
  Train XGBoost on 2014 seasonal weights [Month, sin, cos].
  No year_idx: captures pure seasonal pattern, safe to project forward.

Phase 2 — 2015 Rolling Forecast:
  a) Predict annual 2015 from 2014 H2/H1 momentum × base growth (10%).
  b) Month 1–11: target = remaining_budget × w[m] / sum(w[m..12]).
     After each actual, adjust weights for remaining months (alpha=0.30).
  c) Month 12 = annual_2015 − sum(actuals 1–11).  Annual locked throughout.

Phase 3 — 2016 Full Forecast (no 2016 data used):
  a) Retrain XGBoost on 2014+2015 with year_idx feature.
  b) Predict annual 2016 from 2015 momentum.
  c) Predict weights for year_idx=2, apply to annual 2016.

Weight update rule (Phase 2):
  ratio = actual / target
  w[k] *= 1 + alpha * (ratio - 1)  for all k > current month
  Damped by alpha so one outlier does not dominate future months.
"""

import os
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from itertools import product as iproduct

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CSV_PATH    = os.path.join(BASE_DIR, 'SampleSuperstore.csv')
ALPHA       = 0.30     # weight update learning rate
BASE_GROWTH = 0.10     # base 10% YoY growth before momentum adjustment

METRICS   = ['Sales', 'Profit', 'Customers', 'Orders']
UNIT      = {'Sales': '$', 'Profit': '$', 'Customers': '', 'Orders': ''}
MA        = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
FEAT_BASE = ['Month', 'month_sin', 'month_cos']              # Phase 1 & 2
FEAT_FULL = ['Month', 'month_sin', 'month_cos', 'year_idx']  # Phase 3

# ── 1. Data loading & aggregation ─────────────────────────────────────────────
df_raw = pd.read_csv(CSV_PATH, encoding='latin1')
df_raw['Order Date'] = pd.to_datetime(df_raw['Order Date'], format='%m/%d/%Y')
df_raw['Year']  = df_raw['Order Date'].dt.year
df_raw['Month'] = df_raw['Order Date'].dt.month

def aggregate(years):
    """Aggregate all 4 metrics by Year-Month; fill missing months with 0."""
    sub = df_raw[df_raw['Year'].isin(years)]
    data = {
        'Sales'    : sub.groupby(['Year','Month'])['Sales'].sum(),
        'Profit'   : sub.groupby(['Year','Month'])['Profit'].sum(),
        'Customers': sub.groupby(['Year','Month'])['Customer ID'].nunique(),
        'Orders'   : sub.groupby(['Year','Month'])['Order ID'].nunique(),
    }
    base = pd.DataFrame(
        [(y, m) for y, m in iproduct(years, range(1, 13))],
        columns=['Year', 'Month']
    )
    out = base.merge(pd.DataFrame(data).reset_index(),
                     on=['Year', 'Month'], how='left').fillna(0)
    out['month_sin'] = np.sin(2 * np.pi * out['Month'] / 12)
    out['month_cos'] = np.cos(2 * np.pi * out['Month'] / 12)
    out['year_idx']  = out['Year'] - min(years)
    return out.sort_values(['Year', 'Month']).reset_index(drop=True)

def get_actuals(df, year):
    """Return {metric: {month(int): value(float)}} for a given year."""
    sub = df[df['Year'] == year]
    return {
        metric: {int(m): float(v)
                 for m, v in sub.set_index('Month')[metric]
                                .reindex(range(1, 13), fill_value=0).items()}
        for metric in METRICS
    }

# ── 2. XGBoost helpers ────────────────────────────────────────────────────────
def _train_xgb(X, y):
    model = XGBRegressor(
        n_estimators=400, max_depth=3, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=2,
        random_state=42, verbosity=0,
    )
    model.fit(X, y)
    return model

def _predict_weights(model, features, year_idx=None):
    """Return normalised 12-element weight array."""
    p = pd.DataFrame({'Month'    : range(1, 13),
                      'month_sin': np.sin(2*np.pi*np.arange(1,13)/12),
                      'month_cos': np.cos(2*np.pi*np.arange(1,13)/12)})
    if 'year_idx' in features:
        p['year_idx'] = year_idx
    w = np.clip(model.predict(p[features]), 1e-6, None)
    return w / w.sum()

def train_weights(df_m, features, predict_year_idx=None):
    """
    Train one XGBoost per metric on seasonal weights.
    Returns {metric: 12-element np.array}.
    """
    result = {}
    for metric in METRICS:
        # Clip to 0: targets should never be negative
        vals   = df_m[metric].clip(lower=0)
        annual = df_m.groupby('Year')[metric].transform(
            lambda x: x.clip(lower=0).sum()
        )
        w_raw  = (vals / annual.replace(0, np.nan)).fillna(0)
        model  = _train_xgb(df_m[features], w_raw)
        result[metric] = _predict_weights(model, features, predict_year_idx)
    return result

# ── 3. Annual growth prediction ───────────────────────────────────────────────
def predict_annual(actuals):
    """
    Predict next year's annual target from current year's H2/H1 momentum.
    growth_rate = BASE_GROWTH × clamp(H2/H1, 0.5, 2.5)
    """
    result = {}
    for metric in METRICS:
        a      = actuals[metric]
        h1     = sum(a[m] for m in range(1, 7))
        h2     = sum(a[m] for m in range(7, 13))
        annual = h1 + h2
        mom    = float(np.clip(h2 / abs(h1), 0.5, 2.5)) if abs(h1) > 1 else 1.2
        result[metric] = round(float(annual * (1 + BASE_GROWTH * mom)), 2)
    return result

# ── 4. Weight update (after seeing one month's actual) ────────────────────────
def apply_weight_update(w, actual, target, done_month, alpha=ALPHA):
    """
    After month `done_month` (1-indexed), adjust weights for later months.
    ratio > 1 → overperformed → boost remaining months.
    ratio < 1 → underperformed → trim remaining months.
    done_month+1..12 correspond to 0-indexed k = done_month..11.
    """
    if target == 0:
        return w
    ratio   = float(np.clip(actual / target, 0.1, 5.0))
    updated = w.copy()
    for k in range(done_month, 12):      # 0-indexed
        updated[k] *= (1 + alpha * (ratio - 1))
    return updated

# ── 5. Rolling monthly forecast ───────────────────────────────────────────────
def rolling_forecast(initial_weights, annual_targets, actuals):
    """
    Simulate month-by-month forecast for one year.

    - Month 1–11: target from remaining budget + live seasonal weights.
    - After each actual (month 1–10): update weights for subsequent months.
    - Month 12: annual − sum(actuals 1–11). Annual total is never changed.

    Returns {metric: {month: {'target', 'actual', 'error_pct'}}}
    """
    cur_w   = {m: initial_weights[m].copy() for m in METRICS}
    results = {m: {} for m in METRICS}

    for month in range(1, 13):
        for metric in METRICS:
            w      = cur_w[metric]
            annual = annual_targets[metric]
            spent  = sum(actuals[metric][k] for k in range(1, month))
            rem_bg = annual - spent

            if month < 12:
                rem_w   = w[month - 1:]
                rem_sum = rem_w.sum()
                t = (float(rem_bg * w[month-1] / rem_sum)
                     if rem_sum > 0 else rem_bg / (13 - month))
            else:
                # Derive month 12 from locked annual total
                t = float(annual - sum(actuals[metric][k] for k in range(1, 12)))

            t = round(t, 2)
            a = actuals[metric][month]
            e = round((a - t) / abs(t) * 100, 1) if t != 0 else 0.0

            results[metric][month] = {'target': t, 'actual': a, 'error_pct': e}

            # Update weights after months 1–10 only
            # (month 11 affects only month 12, which is derived anyway)
            if month < 11:
                cur_w[metric] = apply_weight_update(w, a, t, month)

    return results, cur_w   # also return final weights for inspection

# ─────────────────────────────────────────────────────────────────────────────
#  RUN ALL PHASES
# ─────────────────────────────────────────────────────────────────────────────
df_14   = aggregate([2014])
df_1415 = aggregate([2014, 2015])
df_all  = aggregate(list(range(2014, 2018)))

act_14 = get_actuals(df_all, 2014)
act_15 = get_actuals(df_all, 2015)
act_16 = get_actuals(df_all, 2016)

# Phase 1: pure seasonal weights from 2014
w_14 = train_weights(df_14, FEAT_BASE)

# Phase 2: 2015 rolling forecast
ann_15          = predict_annual(act_14)
res_15, w_15upd = rolling_forecast(w_14, ann_15, act_15)

# Phase 3: retrain on 2014+2015, forecast 2016 (year_idx=2 — one step beyond training)
w_16       = train_weights(df_1415, FEAT_FULL, predict_year_idx=2)
ann_16     = predict_annual(act_15)
targets_16 = {
    metric: {m: round(float(w_16[metric][m-1] * ann_16[metric]), 2)
             for m in range(1, 13)}
    for metric in METRICS
}

# ─────────────────────────────────────────────────────────────────────────────
#  PRINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':

    def fmt(value, unit):
        if unit == '$':
            return f"${value:>10,.0f}"
        return f"{value:>11,.0f}"

    W = 76

    # ── Phase 2: 2015 rolling ─────────────────────────────────────────────────
    print('=' * W)
    print(f"{'2015  ROLLING MONTHLY FORECAST':^{W}}")
    print(f"{'XGBoost weights  |  updated after each actual  |  alpha = 0.30':^{W}}")
    print('=' * W)

    for metric in METRICS:
        u       = UNIT[metric]
        ann     = ann_15[metric]
        act_ann = sum(act_15[metric].values())
        gap     = round((act_ann - ann) / ann * 100, 1)

        print(f"\n  {metric}  |  Predicted annual: {u}{ann:>10,.0f}"
              f"   Actual annual: {u}{act_ann:>10,.0f}  ({gap:+.1f}%)")
        print(f"  {'Month':<6}  {'Target':>12}  {'Actual':>12}  {'Error%':>8}  Note")
        print('  ' + '-' * 60)

        for m in range(1, 13):
            r    = res_15[metric][m]
            t, a, e = r['target'], r['actual'], r['error_pct']
            if m == 12:
                note = 'derived (annual lock)'
            elif m == 1:
                note = 'init. weights'
            else:
                note = f'upd. after {MA[m-1]}'
            print(f"  {MA[m]:<6}  {fmt(t,u)}  {fmt(a,u)}  {e:>+7.1f}%  {note}")

        print('  ' + '-' * 60)
        print(f"  {'ANNUAL':<6}  {fmt(ann,u)} (target)  {fmt(act_ann,u)} (actual)")

    # ── Phase 3: 2016 forecast ────────────────────────────────────────────────
    print()
    print('=' * W)
    print(f"{'2016  FULL FORECAST  (no 2016 data used)':^{W}}")
    print(f"{'XGBoost retrained on 2014+2015  |  year_idx=2  |  annual from 2015 momentum':^{W}}")
    print('=' * W)

    for metric in METRICS:
        u       = UNIT[metric]
        ann     = ann_16[metric]
        act_ann = sum(act_16[metric].values())
        gap     = round((act_ann - ann) / ann * 100, 1)
        total_t = sum(targets_16[metric].values())

        print(f"\n  {metric}  |  Forecast annual: {u}{ann:>10,.0f}"
              f"   Actual annual: {u}{act_ann:>10,.0f}  ({gap:+.1f}%)")
        print(f"  {'Month':<6}  {'Forecast':>12}  {'Actual 2016':>12}  {'Error%':>8}")
        print('  ' + '-' * 48)

        for m in range(1, 13):
            t = targets_16[metric][m]
            a = act_16[metric][m]
            e = round((a - t) / abs(t) * 100, 1) if t != 0 else 0.0
            print(f"  {MA[m]:<6}  {fmt(t,u)}  {fmt(a,u)}  {e:>+7.1f}%")

        print('  ' + '-' * 48)
        print(f"  {'TOTAL':<6}  {fmt(total_t,u)}  {fmt(act_ann,u)}")

    # ── Weight evolution summary ──────────────────────────────────────────────
    print()
    print('=' * W)
    print(f"{'SEASONAL WEIGHT EVOLUTION  (Sales)':^{W}}")
    print(f"{'2014 baseline  ->  after 2015 updates  ->  2016 forecast':^{W}}")
    print('=' * W)
    print(f"  {'Month':<6}  {'2014 base':>10}  {'2015 updated':>13}  {'2016 forecast':>14}")
    print('  ' + '-' * 50)
    for m in range(1, 13):
        w14 = w_14['Sales'][m-1]
        w15 = w_15upd['Sales'][m-1]
        w16 = w_16['Sales'][m-1]
        print(f"  {MA[m]:<6}  {w14:>9.2%}  {w15:>12.2%}  {w16:>13.2%}")
    print('=' * W)
