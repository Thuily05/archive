import pandas as pd
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from constants import SALES_TARGET

_here = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(_here, "SampleSuperstore.csv"), encoding="latin1")
df['Order Date'] = pd.to_datetime(df['Order Date'])
df['Year']  = df['Order Date'].dt.year
df['Month'] = df['Order Date'].dt.month

# ── Actual sales theo tung thang nam 2014
actual_2014 = (
    df[df['Year'] == 2014]
    .groupby('Month')['Sales'].sum()
    .reindex(range(1, 13), fill_value=0)
)

# ── Tham so Attainment-based Ratchet
ANNUAL_TARGET   = SALES_TARGET[2014]   # 400_000
BASE_TARGET     = ANNUAL_TARGET / 12   # ~33_333 / thang
GROWTH_RATE     = 0.05                 # tang 5% khi dat or vuot target
ATT_HIGH        = 1.00                 # >= 100% → tang
ATT_LOW         = 0.80                 # <  80%  → ha xuong sat actual

# ── Tinh target tung thang bang Ratchet
results = []
current_target = BASE_TARGET

for month in range(1, 13):
    actual     = actual_2014[month]
    attainment = actual / current_target if current_target > 0 else 0

    if attainment >= ATT_HIGH:
        # Dat hoac vuot → tang target thang sau
        status      = 'DAT'
        next_target = actual * (1 + GROWTH_RATE)
    elif attainment >= ATT_LOW:
        # Gan dat (80-99%) → giu nguyen target
        status      = 'GAN DAT'
        next_target = current_target
    else:
        # Tut xa (< 80%) → ha xuong sat actual de thuc te hon
        status      = 'CHUA DAT'
        next_target = actual * (1 + GROWTH_RATE)

    results.append({
        'Month':        month,
        'Target':       round(current_target, 0),
        'Actual':       round(actual, 0),
        'Attainment_%': round(attainment * 100, 1),
        'Status':       status,
        'Next_Target':  round(next_target, 0),
    })

    current_target = next_target   # ratchet sang thang tiep theo

# ── DataFrame ket qua
TARGET_2014 = pd.DataFrame(results)

# ── Tong ket
total_target = TARGET_2014['Target'].sum()
total_actual = TARGET_2014['Actual'].sum()
overall_att  = total_actual / total_target * 100

if __name__ == '__main__':
    month_names = ['Jan','Feb','Mar','Apr','May','Jun',
                   'Jul','Aug','Sep','Oct','Nov','Dec']
    df_print = TARGET_2014.copy()
    df_print.insert(0, 'Month_Name', month_names)

    print("=" * 70)
    print("  MONTHLY TARGET 2014 – Attainment-based Ratchet")
    print(f"  Annual target : ${ANNUAL_TARGET:,.0f}")
    print(f"  Base/month    : ${BASE_TARGET:,.0f}  |  Growth rate: {GROWTH_RATE*100:.0f}%")
    print("=" * 70)
    print(df_print.to_string(index=False))
    print("=" * 70)
    print(f"  Total Target : ${total_target:,.0f}")
    print(f"  Total Actual : ${total_actual:,.0f}")
    print(f"  Overall Att. : {overall_att:.1f}%")
    print("=" * 70)
