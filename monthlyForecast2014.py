"""
monthlyForecast2014.py
----------------------
Rolling monthly forecast for 2014, starting from given January targets.

Algorithm per month m (m = 1 to 12):
  1. PREDICT  target[m]
       Month 1  : given directly (JAN_TARGET)
       Month 2+: remaining_budget * w[m] / sum(w[m..12])
  2. COMPARE  actual[m] from SampleSuperstore.csv vs target[m]
  3. UPDATE WEIGHTS  w[k] *= 1 + alpha*(actual/target - 1)  for k > m
  4. UPDATE ANNUAL ESTIMATE
       pace = cumulative_actual / cumulative_weight (original)
       annual_est = (1-beta)*annual_est + beta*pace

End-of-year calibration:
  Retrain XGBoost on actual 2014 monthly data -> CALIBRATED_WEIGHTS
  Predict 2015 annual via H2/H1 momentum * 10% base growth

Given January 2014 targets:
  Sales=$50,000  Profit=$5,000  Customers=50  Orders=100

Hyperparameters:
  alpha = 0.30  weight update learning rate
  beta  = 0.50  annual estimate update rate

Exports (for monthlyForecast2015.py):
  CALIBRATED_WEIGHTS   {metric: 12-element np.array}  XGBoost retrained on 2014 actuals
  XGB_MODELS           {metric: XGBRegressor}
  ANNUAL_TARGET_2015   {metric: float}
  FORECAST_2014        {metric: {month: {target, actual, error_pct, annual_est}}}
  ACTUAL_2014          {metric: {month: float}}
"""

import os
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from itertools import product as iproduct

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CSV_PATH    = os.path.join(BASE_DIR, 'SampleSuperstore.csv')
ALPHA       = 0.30
BETA        = 0.50
BASE_GROWTH = 0.10

METRICS   = ['Sales', 'Profit', 'Customers', 'Orders']
UNIT      = {'Sales': '$', 'Profit': '$', 'Customers': '', 'Orders': ''}
MA        = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
FEAT_BASE = ['Month', 'month_sin', 'month_cos']

# ── Given January 2014 targets ────────────────────────────────────────────────
JAN_TARGET = {
    'Sales'    : 50_000,
    'Profit'   :  5_000,
    'Customers':     50,
    'Orders'   :    100,
}

# ── 1. Data ───────────────────────────────────────────────────────────────────
df_raw = pd.read_csv(CSV_PATH, encoding='latin1')
df_raw['Order Date'] = pd.to_datetime(df_raw['Order Date'], format='%m/%d/%Y')
df_raw['Year']  = df_raw['Order Date'].dt.year
df_raw['Month'] = df_raw['Order Date'].dt.month

def aggregate(years):
    sub  = df_raw[df_raw['Year'].isin(years)]
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
    return out.sort_values(['Year', 'Month']).reset_index(drop=True)

def get_actuals(df, year):
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

def _get_weights(model):
    p = pd.DataFrame({
        'Month'    : range(1, 13),
        'month_sin': np.sin(2 * np.pi * np.arange(1, 13) / 12),
        'month_cos': np.cos(2 * np.pi * np.arange(1, 13) / 12),
    })
    w = np.clip(model.predict(p[FEAT_BASE]), 1e-6, None)
    return w / w.sum()

def train_all(df_m):
    """Train one XGBoost per metric. Return (models, weights)."""
    models  = {}
    weights = {}
    for metric in METRICS:
        vals   = df_m[metric].clip(lower=0)
        annual = df_m.groupby('Year')[metric].transform(
                     lambda x: x.clip(lower=0).sum())
        w_raw  = (vals / annual.replace(0, np.nan)).fillna(0)
        model  = _train_xgb(df_m[FEAT_BASE], w_raw)
        models[metric]  = model
        weights[metric] = _get_weights(model)
    return models, weights

# ── 3. Annual growth prediction ───────────────────────────────────────────────
def predict_annual_2015(actuals_14):
    result = {}
    for metric in METRICS:
        a      = actuals_14[metric]
        h1     = sum(a[m] for m in range(1, 7))
        h2     = sum(a[m] for m in range(7, 13))
        annual = h1 + h2
        mom    = float(np.clip(h2 / abs(h1), 0.5, 2.5)) if abs(h1) > 1 else 1.2
        result[metric] = round(float(annual * (1 + BASE_GROWTH * mom)), 2)
    return result

# ─────────────────────────────────────────────────────────────────────────────
#  PHASE 1: Prior seasonal weights (all years as prior knowledge)
# ─────────────────────────────────────────────────────────────────────────────
df_all = aggregate(list(range(2014, 2018)))
ACTUAL_2014 = get_actuals(df_all, 2014)

_, w_prior = train_all(df_all)   # prior seasonal weights

# Initial annual estimate from Jan targets
annual_est = {
    metric: JAN_TARGET[metric] / w_prior[metric][0]
    for metric in METRICS
}

# ─────────────────────────────────────────────────────────────────────────────
#  PHASE 2: Rolling forecast — month by month
# ─────────────────────────────────────────────────────────────────────────────
w_cur        = {m: w_prior[m].copy() for m in METRICS}
FORECAST_2014 = {m: {} for m in METRICS}

for month in range(1, 13):
    for metric in METRICS:
        w   = w_cur[metric]
        w_o = w_prior[metric]
        ann = annual_est[metric]

        # ── Predict target ────────────────────────────────────────────────────
        if month == 1:
            target_m = float(JAN_TARGET[metric])
        else:
            spent   = sum(ACTUAL_2014[metric][k] for k in range(1, month))
            rem_bg  = ann - spent
            rem_w   = w[month - 1:]
            rem_sum = float(rem_w.sum())
            if rem_sum > 0:
                target_m = float(rem_bg * w[month - 1] / rem_sum)
            else:
                target_m = rem_bg / (13 - month)
        target_m = round(target_m, 2)

        # ── Compare with actual ───────────────────────────────────────────────
        actual_m = ACTUAL_2014[metric][month]
        error    = round((actual_m - target_m) / abs(target_m) * 100, 1) if target_m != 0 else 0.0

        FORECAST_2014[metric][month] = {
            'target'    : target_m,
            'actual'    : actual_m,
            'error_pct' : error,
            'annual_est': round(ann, 1),   # annual estimate used for this month's target
        }

        # ── Update seasonal weights ───────────────────────────────────────────
        if target_m != 0:
            ratio   = float(np.clip(actual_m / target_m, 0.1, 5.0))
            updated = w_cur[metric].copy()
            for k in range(month, 12):    # 0-indexed: months m+1 to 12
                updated[k] *= (1 + ALPHA * (ratio - 1))
            w_cur[metric] = updated

        # ── Update annual estimate (pace-based) ───────────────────────────────
        # pace = cumulative actual / cumulative original weight (fraction of year done)
        cum_w   = float(w_o[0:month].sum())
        cum_act = sum(ACTUAL_2014[metric][k] for k in range(1, month + 1))
        if cum_w > 0:
            pace = cum_act / cum_w
            annual_est[metric] = round((1 - BETA) * ann + BETA * pace, 2)

# ─────────────────────────────────────────────────────────────────────────────
#  PHASE 3: End-of-year calibration
# ─────────────────────────────────────────────────────────────────────────────
# Retrain XGBoost on actual 2014 data for clean calibrated weights
df_14 = aggregate([2014])
XGB_MODELS, CALIBRATED_WEIGHTS = train_all(df_14)

# Final annual estimate after all 12 actuals
ANNUAL_EST_2014 = {metric: annual_est[metric] for metric in METRICS}

# Predict 2015 annual
ANNUAL_TARGET_2015 = predict_annual_2015(ACTUAL_2014)

# ─────────────────────────────────────────────────────────────────────────────
#  PRINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':

    def f(value, unit, w=12):
        """Format a number with optional $ prefix."""
        if unit == '$':
            return f"${value:>{w-1},.0f}"
        return f"{value:>{w},.0f}"

    W = 82

    # ── Phase 2: Month-by-month rolling ──────────────────────────────────────
    print('=' * W)
    print(f"{'2014  ROLLING MONTHLY FORECAST':^{W}}")
    print(f"{'Jan target given  |  alpha={:.2f}  beta={:.2f}  base_growth={:.0%}'.format(ALPHA, BETA, BASE_GROWTH):^{W}}")
    print('=' * W)

    for metric in METRICS:
        u        = UNIT[metric]
        ann_init = round(JAN_TARGET[metric] / w_prior[metric][0])
        act_ann  = sum(ACTUAL_2014[metric].values())
        final_ae = ANNUAL_EST_2014[metric]

        print(f"\n  {metric}")
        print(f"  Jan target: {f(JAN_TARGET[metric], u)}  "
              f"Implied annual: {f(ann_init, u, 14)}  "
              f"Actual 2014 annual: {f(act_ann, u, 14)}")
        print(f"  {'Month':<6}  {'Target':>12}  {'Actual':>12}  {'Error%':>8}  "
              f"{'Annual Est.':>14}  Note")
        print('  ' + '-' * 68)

        for m in range(1, 13):
            r         = FORECAST_2014[metric][m]
            t, a, e   = r['target'], r['actual'], r['error_pct']
            ae        = r['annual_est']
            note      = '<-- given' if m == 1 else ''
            print(f"  {MA[m]:<6}  {f(t,u)}  {f(a,u)}  {e:>+7.1f}%  "
                  f"{f(ae,u,14)}  {note}")

        print('  ' + '-' * 68)
        print(f"  Final annual estimate: {f(final_ae, u)}  |  "
              f"Actual annual: {f(act_ann, u)}  |  "
              f"Gap: {round((act_ann - final_ae)/act_ann*100, 1):+.1f}%")

    # ── Phase 3: Calibrated weights ───────────────────────────────────────────
    print()
    print('=' * W)
    print(f"{'CALIBRATED WEIGHTS  (XGBoost retrained on 2014 actuals)':^{W}}")
    print('=' * W)
    print(f"  {'Month':<6}  {'Sales prior':>12}  {'Sales calib':>12}  "
          f"{'Profit calib':>13}  {'Cust. calib':>12}  {'Order calib':>12}")
    print('  ' + '-' * 72)
    for m in range(1, 13):
        wp  = w_prior['Sales'][m-1]
        wcs = CALIBRATED_WEIGHTS['Sales'][m-1]
        wcp = CALIBRATED_WEIGHTS['Profit'][m-1]
        wcc = CALIBRATED_WEIGHTS['Customers'][m-1]
        wco = CALIBRATED_WEIGHTS['Orders'][m-1]
        print(f"  {MA[m]:<6}  {wp:>11.2%}  {wcs:>11.2%}  "
              f"{wcp:>12.2%}  {wcc:>11.2%}  {wco:>11.2%}")
    print('=' * W)

    # ── 2015 Annual Prediction ────────────────────────────────────────────────
    print()
    print('=' * W)
    print(f"{'2015  ANNUAL TARGET PREDICTION':^{W}}")
    print(f"{'From 2014 actual H2/H1 momentum x 10% base growth':^{W}}")
    print('=' * W)
    print(f"\n  {'Metric':<12}  {'2014 Actual':>14}  {'Growth%':>9}  {'2015 Target':>14}")
    print('  ' + '-' * 56)
    for metric in METRICS:
        u       = UNIT[metric]
        act14   = sum(ACTUAL_2014[metric].values())
        tgt15   = ANNUAL_TARGET_2015[metric]
        growth  = round((tgt15 - act14) / act14 * 100, 1) if act14 else 0.0
        print(f"  {metric:<12}  {f(act14, u, 14)}  {growth:>+8.1f}%  {f(tgt15, u, 14)}")

    print()
    print('=' * W)
    print('  EXPORTS for monthlyForecast2015.py:')
    print('    from monthlyForecast2014 import (')
    print('        CALIBRATED_WEIGHTS,   # seasonal weights retrained on 2014 actuals')
    print('        XGB_MODELS,           # XGBoost models per metric')
    print('        ANNUAL_TARGET_2015,   # predicted annual targets for 2015')
    print('        ACTUAL_2014,          # actual monthly data 2014')
    print('        FORECAST_2014,        # monthly targets + actuals 2014')
    print('    )')
    print('=' * W)
