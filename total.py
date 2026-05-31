import pandas as pd
import os

_here = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(_here, "SampleSuperstore.csv"), encoding="latin1")
df['Order Date'] = pd.to_datetime(df['Order Date'])
df['Year'] = df['Order Date'].dt.year

# ── Tong theo tung nam
yearly = df.groupby('Year').agg(
    Total_Sales     = ('Sales',       'sum'),
    Total_Profit    = ('Profit',      'sum'),
    Total_Customers = ('Customer ID', 'nunique'),
    Total_Orders    = ('Order ID',    'nunique'),
).reset_index()

# ── Tong 4 nam
total_row = pd.DataFrame([{
    'Year':            'TOTAL (4Y)',
    'Total_Sales':     yearly['Total_Sales'].sum(),
    'Total_Profit':    yearly['Total_Profit'].sum(),
    'Total_Customers': df['Customer ID'].nunique(),
    'Total_Orders':    df['Order ID'].nunique(),
}])

summary = pd.concat([yearly, total_row], ignore_index=True)

# ── Export bien de file khac import
YEARLY  = yearly.set_index('Year').to_dict(orient='index')
TOTAL_4Y = {
    'Sales':     yearly['Total_Sales'].sum(),
    'Profit':    yearly['Total_Profit'].sum(),
    'Customers': df['Customer ID'].nunique(),
    'Orders':    df['Order ID'].nunique(),
}

if __name__ == '__main__':
    print(summary.to_string(index=False))
