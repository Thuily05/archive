"""
targetMonth2014.py
------------------
Monthly Targets for 2014 using XGBoost seasonal modelling.
Metrics: Sales, Profit, Customers (unique), Orders (unique).

Method (per metric):
  1. Aggregate metric monthly by year from SampleSuperstore.csv.
  2. Compute seasonal weight = monthly value / year total.
  3. Train XGBoost on [Month, sin/cos, year_idx] -> weight.
  4. Predict weights for 2014 (year_idx=0), normalise to sum=1.
  5. Multiply by annual target from target.py.

Annual targets 2014 (from target.py):
  Sales    : $400,000
  Profit   :  $60,000
  Customers:      110
  Orders   :      800
"""

import os
import pandas as pd
import numpy as np
from xgboost import XGBRegressor

# ── Annual targets (from target.py) ───────────────────────────────────────────
ANNUAL = {
    'Sales'    : 400_000,
    'Profit'   :  60_000,
    'Customers':     110,
    'Orders'   :     800,
}

MONTH_NAMES = [
    '', 'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'SampleSuperstore.csv')

# ── 1. Load raw data ───────────────────────────────────────────────────────────
df = pd.read_csv(CSV_PATH, encoding='latin1')
df['Order Date'] = pd.to_datetime(df['Order Date'], format='%m/%d/%Y')
df['Year']       = df['Order Date'].dt.year
df['Month']      = df['Order Date'].dt.month

# ── 2. Monthly aggregation per metric ─────────────────────────────────────────
agg_sales = df.groupby(['Year', 'Month'])['Sales'].sum().rename('value')
agg_profit = df.groupby(['Year', 'Month'])['Profit'].sum().rename('value')
agg_customers = df.groupby(['Year', 'Month'])['Customer ID'].nunique().rename('value')
agg_orders = df.groupby(['Year', 'Month'])['Order ID'].nunique().rename('value')

RAW = {
    'Sales'    : agg_sales,
    'Profit'   : agg_profit,
    'Customers': agg_customers,
    'Orders'   : agg_orders,
}

# ── Helper: build feature df + seasonal weights ───────────────────────────────
def build_monthly(series: pd.Series) -> pd.DataFrame:
    m = series.reset_index()
    m.columns = ['Year', 'Month', 'value']
    m = m.sort_values(['Year', 'Month']).reset_index(drop=True)
    annual = m.groupby('Year')['value'].sum()
    m['annual'] = m['Year'].map(annual)
    m['weight'] = m['value'] / m['annual']
    m['month_sin'] = np.sin(2 * np.pi * m['Month'] / 12)
    m['month_cos'] = np.cos(2 * np.pi * m['Month'] / 12)
    m['year_idx']  = m['Year'] - m['Year'].min()
    return m

FEATURES = ['Month', 'month_sin', 'month_cos', 'year_idx']

# ── Helper: train XGBoost and predict 2014 monthly targets ───────────────────
def xgb_monthly_targets(series: pd.Series, annual_target: float) -> dict:
    monthly = build_monthly(series)

    model = XGBRegressor(
        n_estimators     = 400,
        max_depth        = 3,
        learning_rate    = 0.05,
        subsample        = 0.8,
        colsample_bytree = 0.8,
        min_child_weight = 2,
        random_state     = 42,
        verbosity        = 0,
    )
    model.fit(monthly[FEATURES], monthly['weight'])

    pred_df = pd.DataFrame({
        'Month'     : range(1, 13),
        'month_sin' : np.sin(2 * np.pi * np.arange(1, 13) / 12),
        'month_cos' : np.cos(2 * np.pi * np.arange(1, 13) / 12),
        'year_idx'  : 0,
    })

    weights = np.clip(model.predict(pred_df[FEATURES]), 1e-6, None)
    weights = weights / weights.sum()

    targets = {m: round(float(weights[m - 1] * annual_target), 2) for m in range(1, 13)}
    return targets, weights, model

# ── 3. Compute monthly targets for all metrics ────────────────────────────────
RESULTS   = {}   # {metric: {month: target}}
WEIGHTS   = {}   # {metric: np.array shape (12,)}
MODELS    = {}   # {metric: XGBRegressor}

for metric, series in RAW.items():
    targets, weights, model = xgb_monthly_targets(series, ANNUAL[metric])
    RESULTS[metric] = targets
    WEIGHTS[metric] = weights
    MODELS[metric]  = model

# Convenience exports
TARGET_MONTH_2014          = RESULTS['Sales']
PROFIT_TARGET_MONTH_2014   = RESULTS['Profit']
CUSTOMER_TARGET_MONTH_2014 = RESULTS['Customers']
ORDER_TARGET_MONTH_2014    = RESULTS['Orders']

# ── 4. Print ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Actual 2014 values per metric
    actual_raw = {
        'Sales'    : agg_sales,
        'Profit'   : agg_profit,
        'Customers': agg_customers,
        'Orders'   : agg_orders,
    }
    actual_2014 = {}
    for metric, series in actual_raw.items():
        s = series.reset_index()
        s.columns = ['Year', 'Month', 'value']
        actual_2014[metric] = (
            s[s['Year'] == 2014]
            .set_index('Month')['value']
            .reindex(range(1, 13), fill_value=0)
        )

    W = 72

    for metric in ['Sales', 'Profit', 'Customers', 'Orders']:
        unit    = '$' if metric in ('Sales', 'Profit') else ''
        targets = RESULTS[metric]
        actual  = actual_2014[metric]
        annual  = ANNUAL[metric]
        total   = sum(targets.values())

        print('=' * W)
        title = f"Monthly {metric} Target 2014  (XGBoost)"
        sub   = f"Annual target = {unit}{annual:,.0f}"
        print(f"{title:^{W}}")
        print(f"{sub:^{W}}")
        print('=' * W)
        print(f"  {'Month':<12}  {'Target':>12}  {'Actual 2014':>13}  {'Weight':>7}")
        print('-' * W)
        for m in range(1, 13):
            t = targets[m]
            a = actual[m]
            w = WEIGHTS[metric][m - 1]
            t_fmt = f"{unit}{t:>11,.0f}" if unit else f"{t:>12,.0f}"
            a_fmt = f"{unit}{a:>11,.0f}" if unit else f"{a:>12,.0f}"
            print(f"  {MONTH_NAMES[m]:<12}  {t_fmt}  {a_fmt}  {w:>6.2%}")
        print('-' * W)
        t_fmt = f"{unit}{total:>11,.0f}" if unit else f"{total:>12,.0f}"
        a_fmt = f"{unit}{actual.sum():>11,.0f}" if unit else f"{actual.sum():>12,.0f}"
        print(f"  {'TOTAL':<12}  {t_fmt}  {a_fmt}")
        print()

    # Feature importance summary
    print('=' * W)
    print(f"{'XGBoost Feature Importances':^{W}}")
    print('=' * W)
    print(f"  {'Feature':<14}  {'Sales':>8}  {'Profit':>8}  {'Customers':>10}  {'Orders':>8}")
    print('-' * W)
    for feat in FEATURES:
        vals = [MODELS[m].feature_importances_[FEATURES.index(feat)] for m in ['Sales', 'Profit', 'Customers', 'Orders']]
        print(f"  {feat:<14}  {vals[0]:>8.4f}  {vals[1]:>8.4f}  {vals[2]:>10.4f}  {vals[3]:>8.4f}")
    print('=' * W)
