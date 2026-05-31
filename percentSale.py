import pandas as pd
import os
from total import YEARLY, TOTAL_4Y

_here = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(_here, "SampleSuperstore.csv"), encoding="latin1")
df['Order Date'] = pd.to_datetime(df['Order Date'])
df['Year'] = df['Order Date'].dt.year

DIMENSIONS = ['Region', 'Segment', 'Category', 'Sub-Category']

# ── % theo tung nam
BY_YEAR = {}
for dim in DIMENSIONS:
    BY_YEAR[dim] = {}
    for year in sorted(YEARLY.keys()):
        total_year = YEARLY[year]['Total_Sales']
        grp = (df[df['Year'] == year]
               .groupby(dim)['Sales'].sum()
               .reset_index()
               .rename(columns={'Sales': 'Actual_Sales'}))
        grp['Pct_Sales'] = (grp['Actual_Sales'] / total_year * 100).round(2)
        grp['Year'] = year
        BY_YEAR[dim][year] = grp

# ── % tong 4 nam
TOTAL = {}
for dim in DIMENSIONS:
    total_all = TOTAL_4Y['Sales']
    grp = (df.groupby(dim)['Sales'].sum()
             .reset_index()
             .rename(columns={'Sales': 'Actual_Sales'}))
    grp['Pct_Sales'] = (grp['Actual_Sales'] / total_all * 100).round(2)
    TOTAL[dim] = grp


if __name__ == '__main__':
    for dim in DIMENSIONS:
        print(f"\n{'='*55}")
        print(f"  % SALES – {dim.upper()}")
        print(f"{'='*55}")
        for year, tbl in BY_YEAR[dim].items():
            print(f"\n  [{year}]")
            print(tbl.to_string(index=False))
        print(f"\n  [TOTAL 4Y]")
        print(TOTAL[dim].to_string(index=False))
