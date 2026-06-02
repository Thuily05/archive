"""
monthlyForecast2017.py
----------------------
Rolling monthly forecast for 2017, using calibrated metrics from monthlyForecast2016.

Initial state (imported from monthlyForecast2016.py):
  CALIBRATED_WEIGHTS  XGBoost weights trained on 2016 actuals
  ANNUAL_TARGET_2017  predicted annual from 2016 H2/H1 momentum

Exports:
  CALIBRATED_WEIGHTS   {metric: np.array}
  XGB_MODELS           {metric: XGBRegressor}
  ANNUAL_TARGET_2018   {metric: float}  (projected, no 2018 data)
  FORECAST_2017        {metric: {month: {target, actual, error_pct, annual_est}}}
  ACTUAL_2017          {metric: {month: float}}
  ANNUAL_TARGET_2017   {metric: float}  kept for audit trail
"""

import os
import sys
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

# ── Import calibrated state from 2016 ────────────────────────────────────────
sys.path.insert(0, BASE_DIR)
from monthlyForecast2016 import (
    CALIBRATED_WEIGHTS as W_INIT,
    ANNUAL_TARGET_2017 as ANN_INIT,
)

# ── Data ──────────────────────────────────────────────────────────────────────
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

def _train_xgb(X, y):
    m = XGBRegressor(n_estimators=400, max_depth=3, learning_rate=0.05,
                     subsample=0.8, colsample_bytree=0.8, min_child_weight=2,
                     random_state=42, verbosity=0)
    m.fit(X, y)
    return m

def _get_weights(model):
    p = pd.DataFrame({'Month'    : range(1, 13),
                      'month_sin': np.sin(2*np.pi*np.arange(1,13)/12),
                      'month_cos': np.cos(2*np.pi*np.arange(1,13)/12)})
    w = np.clip(model.predict(p[FEAT_BASE]), 1e-6, None)
    return w / w.sum()

def train_all(df_m):
    models, weights = {}, {}
    for metric in METRICS:
        vals   = df_m[metric].clip(lower=0)
        annual = df_m.groupby('Year')[metric].transform(
                     lambda x: x.clip(lower=0).sum())
        w_raw  = (vals / annual.replace(0, np.nan)).fillna(0)
        model  = _train_xgb(df_m[FEAT_BASE], w_raw)
        models[metric]  = model
        weights[metric] = _get_weights(model)
    return models, weights

def predict_annual_next(actuals):
    result = {}
    for metric in METRICS:
        a      = actuals[metric]
        h1     = sum(a[m] for m in range(1, 7))
        h2     = sum(a[m] for m in range(7, 13))
        annual = h1 + h2
        mom    = float(np.clip(h2 / abs(h1), 0.5, 2.5)) if abs(h1) > 1 else 1.2
        result[metric] = round(float(annual * (1 + BASE_GROWTH * mom)), 2)
    return result

# ── Load actuals ──────────────────────────────────────────────────────────────
df_all      = aggregate(list(range(2014, 2018)))
ACTUAL_2017 = get_actuals(df_all, 2017)

# ── Initial state ─────────────────────────────────────────────────────────────
w_orig     = {m: W_INIT[m].copy() for m in METRICS}
w_cur      = {m: W_INIT[m].copy() for m in METRICS}
annual_est = {m: float(ANN_INIT[m]) for m in METRICS}

# ── Rolling forecast ──────────────────────────────────────────────────────────
FORECAST_2017 = {m: {} for m in METRICS}

for month in range(1, 13):
    for metric in METRICS:
        w   = w_cur[metric]
        w_o = w_orig[metric]
        ann = annual_est[metric]

        spent    = sum(ACTUAL_2017[metric][k] for k in range(1, month))
        rem_bg   = ann - spent
        rem_w    = w[month - 1:]
        rem_sum  = float(rem_w.sum())
        target_m = (float(rem_bg * w[month-1] / rem_sum)
                    if rem_sum > 0 else rem_bg / (13 - month))
        target_m = round(target_m, 2)

        actual_m = ACTUAL_2017[metric][month]
        error    = round((actual_m - target_m) / abs(target_m) * 100, 1) if target_m != 0 else 0.0

        FORECAST_2017[metric][month] = {
            'target'    : target_m,
            'actual'    : actual_m,
            'error_pct' : error,
            'annual_est': round(ann, 1),
        }

        if target_m != 0:
            ratio   = float(np.clip(actual_m / target_m, 0.1, 5.0))
            updated = w_cur[metric].copy()
            for k in range(month, 12):
                updated[k] *= (1 + ALPHA * (ratio - 1))
            w_cur[metric] = updated

        cum_w   = float(w_o[0:month].sum())
        cum_act = sum(ACTUAL_2017[metric][k] for k in range(1, month + 1))
        if cum_w > 0:
            pace = cum_act / cum_w
            annual_est[metric] = round((1 - BETA) * ann + BETA * pace, 2)

# ── End-of-year calibration ───────────────────────────────────────────────────
df_17 = aggregate([2017])
XGB_MODELS, CALIBRATED_WEIGHTS = train_all(df_17)

ANNUAL_EST_2017    = {metric: annual_est[metric] for metric in METRICS}
ANNUAL_TARGET_2017 = ANN_INIT
ANNUAL_TARGET_2018 = predict_annual_next(ACTUAL_2017)
SUM_MONTHLY_2017   = {
    metric: round(sum(FORECAST_2017[metric][m]['target'] for m in range(1, 13)), 2)
    for metric in METRICS
}

# ── Print ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':

    def f(value, unit, w=12):
        return f"${value:>{w-1},.0f}" if unit == '$' else f"{value:>{w},.0f}"

    W = 82

    print('=' * W)
    print(f"{'2017  ROLLING MONTHLY FORECAST':^{W}}")
    print(f"{'Initial weights from 2016  |  alpha=0.30  beta=0.50  base_growth=10%':^{W}}")
    print('=' * W)

    for metric in METRICS:
        u        = UNIT[metric]
        ann_i    = ANN_INIT[metric]
        act_ann  = sum(ACTUAL_2017[metric].values())
        final_ae = ANNUAL_EST_2017[metric]

        print(f"\n  {metric}")
        print(f"  Annual target (from 2016): {f(ann_i, u, 14)}  "
              f"Actual 2017 annual: {f(act_ann, u, 14)}")
        print(f"  {'Month':<6}  {'Target':>12}  {'Actual':>12}  {'Error%':>8}  {'Annual Est.':>14}")
        print('  ' + '-' * 62)
        for m in range(1, 13):
            r       = FORECAST_2017[metric][m]
            t, a, e = r['target'], r['actual'], r['error_pct']
            ae      = r['annual_est']
            print(f"  {MA[m]:<6}  {f(t,u)}  {f(a,u)}  {e:>+7.1f}%  {f(ae,u,14)}")
        print('  ' + '-' * 62)
        print(f"  Final annual estimate: {f(final_ae, u)}  |  "
              f"Actual annual: {f(act_ann, u)}  |  "
              f"Gap: {round((act_ann - final_ae)/act_ann*100,1):+.1f}%")

    print()
    print('=' * W)
    print(f"{'2017  YEAR-END COMPARISON':^{W}}")
    print('=' * W)
    print(f"  {'Metric':<12}  {'Predicted annual':>17}  {'Sum monthly':>12}  "
          f"{'Final est.':>12}  {'Actual 2017':>12}")
    print(f"  {'':12}  {'(2016 output)':>17}  {'(rolling)':>12}  "
          f"{'(after 12m)':>12}  {'':>12}")
    print('  ' + '-' * 72)
    for metric in METRICS:
        u       = UNIT[metric]
        pred_a  = ANN_INIT[metric]
        sum_m   = SUM_MONTHLY_2017[metric]
        final_e = ANNUAL_EST_2017[metric]
        act_a   = sum(ACTUAL_2017[metric].values())
        g_pred  = round((pred_a  - act_a) / act_a * 100, 1)
        g_sum   = round((sum_m   - act_a) / act_a * 100, 1)
        g_fin   = round((final_e - act_a) / act_a * 100, 1)
        print(f"  {metric:<12}  {f(pred_a,u,17)}  {f(sum_m,u,12)}  "
              f"{f(final_e,u,12)}  {f(act_a,u,12)}")
        print(f"  {'':12}  {'Gap: '+str(g_pred)+'%':>17}  "
              f"{'Gap: '+str(g_sum)+'%':>12}  "
              f"{'Gap: '+str(g_fin)+'%':>12}")
    print('=' * W)

    print()
    print('=' * W)
    print(f"{'CALIBRATED WEIGHTS  (XGBoost retrained on 2017 actuals)':^{W}}")
    print('=' * W)
    print(f"  {'Month':<6}  {'Sales 2016':>11}  {'Sales 2017':>11}  "
          f"{'Profit 2017':>12}  {'Cust. 2017':>11}  {'Order 2017':>11}")
    print('  ' + '-' * 69)
    for m in range(1, 13):
        w16 = W_INIT['Sales'][m-1]
        wcs = CALIBRATED_WEIGHTS['Sales'][m-1]
        wcp = CALIBRATED_WEIGHTS['Profit'][m-1]
        wcc = CALIBRATED_WEIGHTS['Customers'][m-1]
        wco = CALIBRATED_WEIGHTS['Orders'][m-1]
        print(f"  {MA[m]:<6}  {w16:>10.2%}  {wcs:>10.2%}  "
              f"{wcp:>11.2%}  {wcc:>10.2%}  {wco:>10.2%}")
    print('=' * W)

    print()
    print('=' * W)
    print(f"{'2018  ANNUAL TARGET PREDICTION  (projected — no 2018 data)':^{W}}")
    print(f"{'From 2017 actual H2/H1 momentum x 10% base growth':^{W}}")
    print('=' * W)
    print(f"\n  {'Metric':<12}  {'2017 Actual':>14}  {'Growth%':>9}  {'2018 Target':>14}")
    print('  ' + '-' * 56)
    for metric in METRICS:
        u      = UNIT[metric]
        act17  = sum(ACTUAL_2017[metric].values())
        tgt18  = ANNUAL_TARGET_2018[metric]
        growth = round((tgt18 - act17) / act17 * 100, 1) if act17 else 0.0
        print(f"  {metric:<12}  {f(act17,u,14)}  {growth:>+8.1f}%  {f(tgt18,u,14)}")

    print()
    print('=' * W)
    print('  NOTE: 2018 data not available in SampleSuperstore.csv.')
    print('  ANNUAL_TARGET_2018 is a forward projection only.')
    print('=' * W)
