import pandas as pd
import numpy as np

def calculate_goal_weights(df,
                            sales_goal  = 2_600_000,
                            profit_goal = 370_000,
                            total_years = 5,
                            data_years  = 4):
    """
    Tinh trong so phan bo muc tieu (Sales & Profit) xuong tung dimension
    dua tren dong gop lich su.

    Returns: dict { dimension: DataFrame }
    """
    PACE = data_years / total_years  # 0.80

    df = df.copy()
    df['Order Date'] = pd.to_datetime(df['Order Date'])
    df['Margin']     = df['Profit'] / df['Sales']

    total_sales  = df['Sales'].sum()
    total_profit = df['Profit'].sum()

    dimensions = {
        'Region':        ['Region'],
        'Category':      ['Category'],
        'Sub-Category':  ['Sub-Category', 'Category'],
        'Segment':       ['Segment'],
        'Region x Cat':  ['Region', 'Category'],
    }

    results = {}

    for label, cols in dimensions.items():
        grp = df.groupby(cols).agg(
            Sales       = ('Sales',    'sum'),
            Profit      = ('Profit',   'sum'),
            Orders      = ('Order ID', 'nunique'),
            Avg_Margin  = ('Margin',   'mean'),
        ).reset_index()

        # Ty trong dong gop
        grp['Sales_weight']  = grp['Sales']  / total_sales
        grp['Profit_weight'] = grp['Profit'] / total_profit

        # Buoc 1: % dong gop so voi tong hien tai
        grp['Sales_%_Total']  = (grp['Sales_weight']  * 100).round(2)
        grp['Profit_%_Total'] = (grp['Profit_weight'] * 100).round(2)

        # Buoc 2: expectPercent = % dong gop lich su (dung lam co so phan bo)
        # Buoc 3: Expect = expectPercent * (target * PACE)
        #   expect_sales  = Sales_%  * (2_600_000 * 80%)
        #   expect_profit = Profit_% * (  370_000 * 80%)
        pace_sales  = sales_goal  * PACE   # 2_080_000
        pace_profit = profit_goal * PACE   # 296_000

        grp['Expect_Sales']  = (grp['Sales_weight']  * pace_sales ).round(0).astype(int)
        grp['Expect_Profit'] = (grp['Profit_weight'] * pace_profit).round(0).astype(int)

        # Margin tuong ung
        grp['Margin_Target_%'] = (grp['Expect_Profit'] / grp['Expect_Sales'] * 100).round(1)

        # So sanh thuc te vs ky vong
        grp['Sales_vs_Exp_%']  = (grp['Sales']  / grp['Expect_Sales']  * 100).round(1)
        grp['Profit_vs_Exp_%'] = (grp['Profit'] / grp['Expect_Profit'] * 100).where(
            grp['Expect_Profit'] != 0, other=0).round(1)

        def status_sales(pct):
            if pct >= 100:  return 'DAT KY VONG'
            elif pct >= 80: return 'CAN THEO DOI'
            else:           return 'CHUA DAT'

        def status_profit(pct, expect):
            if expect <= 0:  return 'BI LO'
            if pct >= 100:   return 'DAT KY VONG'
            elif pct >= 80:  return 'CAN THEO DOI'
            else:            return 'CHUA DAT'

        grp['Sales_Status']  = grp['Sales_vs_Exp_%'].apply(status_sales)
        grp['Profit_Status'] = grp.apply(
            lambda r: status_profit(r['Profit_vs_Exp_%'], r['Expect_Profit']), axis=1)

        results[label] = grp

    # ── Summary tong hop
    print(f"{'='*65}")
    print(f"  GOAL WEIGHT DECOMPOSITION")
    print(f"  Sales Goal 5Y : ${sales_goal:,.0f}  |  Profit Goal 5Y: ${profit_goal:,.0f}")
    print(f"  Pace {data_years}/{total_years} = {PACE*100:.0f}%  =>  Expect Sales: ${sales_goal*PACE:,.0f}  |  Expect Profit: ${profit_goal*PACE:,.0f}")
    print(f"  Expect component = %_Total x Expect_Total")
    print(f"{'='*65}")

    for label, tbl in results.items():
        print(f"\n{'─'*65}")
        print(f"  [{label.upper()}]")
        print(f"{'─'*65}")
        dim_cols = dimensions[label]   # fix: dung dung cols cua tung dimension
        display_cols = dim_cols + [
            'Sales', 'Sales_%_Total', 'Expect_Sales', 'Sales_vs_Exp_%', 'Sales_Status',
            'Profit', 'Profit_%_Total', 'Expect_Profit', 'Profit_vs_Exp_%', 'Profit_Status',
            'Margin_Target_%']
        print(tbl[display_cols].to_string(index=False))

    # ── Luu ket qua thanh anh
    import matplotlib.pyplot as plt
    import os

    status_colors = {
        'DAT KY VONG':  '#d4f0e3',
        'CAN THEO DOI': '#fff3cd',
        'CHUA DAT':     '#fde8e8',
        'BI LO':        '#f0d0d0',
    }
    header_color  = '#2c3e50'
    row_colors    = ['#f9f9f9', '#ffffff']

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'expectKPIsOutput/average')
    os.makedirs(output_dir, exist_ok=True)

    for label, tbl in results.items():
        cols_key = dimensions[label]
        display_cols = cols_key + [
            'Sales', 'Sales_%_Total', 'Expect_Sales', 'Sales_vs_Exp_%', 'Sales_Status',
            'Profit', 'Profit_%_Total', 'Expect_Profit', 'Profit_vs_Exp_%', 'Profit_Status',
            'Margin_Target_%'
        ]
        t = tbl[display_cols].copy()

        # Format so dep
        for c in ['Sales', 'Expect_Sales', 'Profit', 'Expect_Profit']:
            t[c] = t[c].apply(lambda v: f'${v/1000:.1f}K')
        for c in ['Sales_%_Total', 'Profit_%_Total',
                  'Sales_vs_Exp_%', 'Profit_vs_Exp_%', 'Margin_Target_%']:
            t[c] = t[c].apply(lambda v: f'{v:.1f}%')

        col_labels = [c.replace('_', ' ') for c in display_cols]
        n_rows, n_cols = t.shape

        fig_w = max(14, n_cols * 1.4)
        fig_h = max(2.5, n_rows * 0.55 + 1.5)
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        ax.axis('off')

        tbl_obj = ax.table(
            cellText   = t.values,
            colLabels  = col_labels,
            cellLoc    = 'center',
            loc        = 'center'
        )
        tbl_obj.auto_set_font_size(False)
        tbl_obj.set_fontsize(9)
        tbl_obj.scale(1, 1.6)

        # Header style
        for j in range(n_cols):
            cell = tbl_obj[0, j]
            cell.set_facecolor(header_color)
            cell.set_text_props(color='white', fontweight='bold')

        # Row style + status color
        for i in range(n_rows):
            for j in range(n_cols):
                cell = tbl_obj[i + 1, j]
                col_name = display_cols[j]
                if col_name in ('Sales_Status', 'Profit_Status'):
                    raw_status = tbl.iloc[i][col_name]
                    cell.set_facecolor(status_colors.get(raw_status, '#ffffff'))
                else:
                    cell.set_facecolor(row_colors[i % 2])

        fig.suptitle(
            f'[{label.upper()}]  |  Sales Goal 5Y: $2,600,000  |  Pace {data_years}/{total_years} = {PACE*100:.0f}%',
            fontsize=11, fontweight='bold', y=0.97
        )

        fname = os.path.join(output_dir, f'goal_weights_{label.replace(" ", "_")}.png')
        plt.savefig(fname, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f'  Saved: {fname}')

    print(f"\nDone. {len(results)} images saved to: {output_dir}")
    return results


# ── Chay ham
import os as _os
_here = _os.path.dirname(_os.path.abspath(__file__))
df = pd.read_csv(_os.path.join(_here, "SampleSuperstore.csv"), encoding="latin1")

weights = calculate_goal_weights(
    df,
    sales_goal  = 2_600_000,
    profit_goal = 370_000,
    total_years = 5,
    data_years  = 4
)

# Lay ket qua tung dimension
region_weights   = weights['Region']
category_weights = weights['Category']
segment_weights  = weights['Segment']
subcat_weights   = weights['Sub-Category']
