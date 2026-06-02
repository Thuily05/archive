# ============================================================
#  TARGETS – Annual KPI Goals by Year
#  Source: suggestTargetConst.py (SUGGESTED_RANGES)
#
#  Tier strategy (per year):
#    2014 : Challenging  (1.20x baseline)
#    2015 : Achievable   (1.10x baseline)
#    2016 : Challenging  (1.20x baseline)
#    2017 : Challenging  (1.20x baseline)
# ============================================================

SALES_TARGET = {
    2014: 480_000,      # Challenging  (baseline $400K × 1.20)
    2015: 639_633,      # Achievable   (baseline $581K × 1.10)
    2016: 676_353,      # Challenging  (baseline $564K × 1.20)
    2017: 852_150,      # Challenging  (baseline $710K × 1.20)
}

PROFIT_TARGET = {
    2014:  72_000,      # Challenging  (baseline $60K × 1.20)
    2015:  67_031,      # Achievable   (baseline $61K × 1.10)
    2016:  87_783,      # Challenging  (baseline $73K × 1.20)
    2017: 117_186,      # Challenging  (baseline $98K × 1.20)
}

CUSTOMER_TARGET = {
    2014:   132,        # Challenging  (baseline 110 × 1.20)
    2015: 1_205,        # Achievable   (baseline 1,095 × 1.10)
    2016: 1_368,        # Challenging  (baseline 1,140 × 1.20)
    2017: 1_700,        # Challenging  (baseline 1,417 × 1.20)
}

ORDER_TARGET = {
    2014:   960,        # Challenging  (baseline 800 × 1.20)
    2015: 1_270,        # Achievable   (baseline 1,155 × 1.10)
    2016: 1_482,        # Challenging  (baseline 1,235 × 1.20)
    2017: 1_859,        # Challenging  (baseline 1,549 × 1.20)
}

# ── Totals (4-year: 2014–2017) ────────────────────────────────────────────────
TOTAL_SALES_TARGET    = sum(SALES_TARGET.values())      # 2_648_136
TOTAL_PROFIT_TARGET   = sum(PROFIT_TARGET.values())     #   344_000
TOTAL_CUSTOMER_TARGET = sum(CUSTOMER_TARGET.values())   #     4_405
TOTAL_ORDER_TARGET    = sum(ORDER_TARGET.values())      #     5_571

# ── Metadata ──────────────────────────────────────────────────────────────────
TIER_BY_YEAR = {
    2014: 'Challenging',
    2015: 'Achievable',
    2016: 'Challenging',
    2017: 'Challenging',
}

DATA_YEARS  = 4
TOTAL_YEARS = 5
PACE        = DATA_YEARS / TOTAL_YEARS   # 0.80
