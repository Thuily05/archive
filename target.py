# ============================================================
#  TARGETS – Annual KPI Goals by Year
#  5-Year Plan: 2014 – 2018
#  Total Sales Goal  : $2,600,000
#  Total Profit Goal :   $370,000
# ============================================================

SALES_TARGET = {
    2014: 400_000,
}

PROFIT_TARGET = {
    2014:  60_000,
}

CUSTOMER_TARGET = {
    2014: 110,
}

ORDER_TARGET = {
    2014:  800,
}

# ── Tong kich luy 5 nam (kiem tra)
TOTAL_SALES_GOAL    = sum(SALES_TARGET.values())    # 3_000_000
TOTAL_PROFIT_GOAL   = sum(PROFIT_TARGET.values())   # 700_000
TOTAL_CUSTOMER_GOAL = sum(CUSTOMER_TARGET.values()) # 1000
TOTAL_ORDER_GOAL    = sum(ORDER_TARGET.values())    # 7500

# ── Chu ky hien tai
DATA_YEARS  = 4   # so nam co du lieu thuc te (2014-2017)
TOTAL_YEARS = 5
PACE        = DATA_YEARS / TOTAL_YEARS   # 0.80
