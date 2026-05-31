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
        total_year = YEARLY[year]['Total_Customers']
        grp = (df[df['Year'] == year]
               .groupby(dim)['Customer ID'].nunique()
               .reset_index()
               .rename(columns={'Customer ID': 'Actual_Customers'}))
        grp['Pct_Customers'] = (grp['Actual_Customers'] / total_year * 100).round(2)
        grp['Year'] = year
        BY_YEAR[dim][year] = grp

# ── % tong 4 nam
TOTAL = {}
for dim in DIMENSIONS:
    total_all = TOTAL_4Y['Customers']
    grp = (df.groupby(dim)['Customer ID'].nunique()
             .reset_index()
             .rename(columns={'Customer ID': 'Actual_Customers'}))
    grp['Pct_Customers'] = (grp['Actual_Customers'] / total_all * 100).round(2)
    TOTAL[dim] = grp


if __name__ == '__main__':
    print("Luu y: 1 customer co the mua nhieu Category/Sub-Category")
    print("=> Tong % theo Category/Sub-Category co the > 100%\n")
    for dim in DIMENSIONS:
        print(f"\n{'='*55}")
        print(f"  % CUSTOMERS – {dim.upper()}")
        print(f"{'='*55}")
        for year, tbl in BY_YEAR[dim].items():
            print(f"\n  [{year}]")
            print(tbl.to_string(index=False))
        print(f"\n  [TOTAL 4Y]")
        print(TOTAL[dim].to_string(index=False))
