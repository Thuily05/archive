# ============================================================
#  TARGETS – Annual KPI Goals by Year
#  5-Year Plan: 2014 – 2018
#  Total Sales Goal  : $2,600,000
#  Total Profit Goal :   $370,000
# ============================================================

SALES_TARGET = {
    2014: 400_000,
    2015: 470_000,
    2016: 530_000,
    2017: 600_000,
    2018: 600_000,   # du kien
}

PROFIT_TARGET = {
    2014:  50_000,
    2015:  65_000,
    2016:  80_000,
    2017:  90_000,
    2018:  85_000,   # du kien
}

CUSTOMER_TARGET = {
    2014: 100,
    2015: 160,
    2016: 200,
    2017: 240,
    2018: 200,   # du kien
}

ORDER_TARGET = {
    2014:  800,
    2015: 1_100,
    2016: 1_400,
    2017: 1_700,
    2018: 1_500,   # du kien (co the giam do thi truong bao hoa)
}

# ── Tong kich luy 5 nam (kiem tra)
TOTAL_SALES_GOAL    = sum(SALES_TARGET.values())    # 2_600_000
TOTAL_PROFIT_GOAL   = sum(PROFIT_TARGET.values())   # 370_000
TOTAL_CUSTOMER_GOAL = sum(CUSTOMER_TARGET.values()) # 900
TOTAL_ORDER_GOAL    = sum(ORDER_TARGET.values())    # 6_500

# ── Chu ky hien tai
DATA_YEARS  = 4   # so nam co du lieu thuc te (2014-2017)
TOTAL_YEARS = 5
PACE        = DATA_YEARS / TOTAL_YEARS   # 0.80
