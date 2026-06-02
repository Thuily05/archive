# Predict Target 2014 — Rolling Monthly Forecast

> **Model:** XGBoost Seasonal Weights + Adaptive Annual Estimate  
> **Method:** Given Jan target → actual comparison → weight update → next month predict  
> **Hyperparameters:** alpha = 0.30 | beta = 0.50 | base_growth = 10%

---

## Given January 2014 Targets

| Metric    | Jan Target   |
|-----------|-------------:|
| Sales     | $50,000      |
| Profit    | $5,000       |
| Customers | 50           |
| Orders    | 100          |

---

## Sales — Rolling Forecast

**Implied annual (from Jan target):** $1,284,158  
**Actual 2014 annual:** $484,247  
**Final annual estimate (after 12 months):** $483,174 → Gap: **+0.2%**

| Month | Target ($) | Actual ($) | Error% | Annual Est. ($) |
|-------|----------:|----------:|-------:|----------------:|
| Jan   | 50,000    | 14,237    | -71.5% | 1,284,158       |
| Feb   | 20,296    | 4,520     | -77.7% | 824,904         |
| Mar   | 52,655    | 55,691    | +5.8%  | 561,322         |
| Apr   | 32,719    | 28,295    | -13.5% | 522,482         |
| May   | 33,720    | 23,648    | -29.9% | 499,382         |
| Jun   | 31,536    | 34,595    | +9.7%  | 473,477         |
| Jul   | 30,299    | 33,946    | +12.0% | 468,311         |
| Aug   | 32,090    | 27,909    | -13.0% | 470,773         |
| Sep   | 64,166    | 81,777    | +27.4% | 467,354         |
| Oct   | 39,148    | 31,453    | -19.7% | 480,651         |
| Nov   | 74,219    | 78,629    | +5.9%  | 479,712         |
| Dec   | 67,400    | 69,546    | +3.2%  | 482,101         |
| **TOTAL** | — | **484,247** | — | **483,174** |

---

## Profit — Rolling Forecast

**Implied annual (from Jan target):** $124,076  
**Actual 2014 annual:** $49,544  
**Final annual estimate (after 12 months):** $47,487 → Gap: **+4.2%**

| Month | Target ($) | Actual ($) | Error% | Annual Est. ($) |
|-------|----------:|----------:|-------:|----------------:|
| Jan   | 5,000     | 2,450     | -51.0% | 124,076         |
| Feb   | 3,129     | 862       | -72.4% | 92,439          |
| Mar   | 6,331     | 499       | -92.1% | 68,702          |
| Apr   | 2,383     | 3,489     | +46.4% | 46,016          |
| May   | 3,132     | 2,739     | -12.6% | 40,340          |
| Jun   | 2,831     | 4,977     | +75.8% | 37,756          |
| Jul   | 1,727     | -841      | -148.7%| 39,825          |
| Aug   | 3,022     | 5,318     | +76.0% | 37,495          |
| Sep   | 4,859     | 8,328     | +71.4% | 39,033          |
| Oct   | 3,953     | 3,448     | -12.8% | 42,334          |
| Nov   | 5,438     | 9,292     | +70.9% | 43,004          |
| Dec   | 4,869     | 8,984     | +84.5% | 45,429          |
| **TOTAL** | — | **49,544** | — | **47,487** |

---

## Customers — Rolling Forecast

**Implied annual (from Jan target):** 1,378  
**Actual 2014 annual:** 923  
**Final annual estimate (after 12 months):** 917 → Gap: **+0.7%**

| Month | Target | Actual | Error% | Annual Est. |
|-------|-------:|-------:|-------:|------------:|
| Jan   | 50     | 32     | -36.0% | 1,378       |
| Feb   | 38     | 27     | -29.7% | 1,130       |
| Mar   | 74     | 69     | -6.8%  | 987         |
| Apr   | 66     | 64     | -3.5%  | 937         |
| May   | 69     | 67     | -2.3%  | 916         |
| Jun   | 66     | 63     | -4.6%  | 907         |
| Jul   | 63     | 65     | +3.6%  | 899         |
| Aug   | 63     | 70     | +10.8% | 899         |
| Sep   | 120    | 118    | -1.6%  | 906         |
| Oct   | 75     | 75     | +0.1%  | 906         |
| Nov   | 131    | 139    | +5.8%  | 906         |
| Dec   | 122    | 134    | +10.1% | 911         |
| **TOTAL** | — | **923** | — | **917** |

---

## Orders — Rolling Forecast

**Implied annual (from Jan target):** 2,908  
**Actual 2014 annual:** 969  
**Final annual estimate (after 12 months):** 966 → Gap: **+0.3%**

| Month | Target | Actual | Error% | Annual Est. |
|-------|-------:|-------:|-------:|------------:|
| Jan   | 100    | 32     | -68.0% | 2,908       |
| Feb   | 63     | 28     | -55.3% | 1,920       |
| Mar   | 103    | 71     | -31.2% | 1,412       |
| Apr   | 84     | 66     | -21.1% | 1,182       |
| May   | 81     | 69     | -14.4% | 1,068       |
| Jun   | 74     | 66     | -10.4% | 1,009       |
| Jul   | 67     | 65     | -3.2%  | 977         |
| Aug   | 66     | 72     | +8.5%  | 963         |
| Sep   | 132    | 130    | -1.7%  | 963         |
| Oct   | 80     | 78     | -2.4%  | 961         |
| Nov   | 145    | 151    | +4.0%  | 959         |
| Dec   | 134    | 141    | +4.9%  | 962         |
| **TOTAL** | — | **969** | — | **966** |

---

## Calibrated Weights (XGBoost retrained on 2014 actuals)

| Month | Sales prior | Sales calib | Profit calib | Cust. calib | Order calib |
|-------|------------:|------------:|-------------:|------------:|------------:|
| Jan   | 3.89%       | 3.04%       | 4.98%        | 3.58%       | 3.43%       |
| Feb   | 2.41%       | 0.76%       | 1.50%        | 2.78%       | 2.72%       |
| Mar   | 9.09%       | 11.53%      | 1.03%        | 7.51%       | 7.35%       |
| Apr   | 6.18%       | 5.92%       | 7.05%        | 7.02%       | 6.90%       |
| May   | 6.67%       | 4.90%       | 5.73%        | 7.12%       | 7.00%       |
| Jun   | 6.52%       | 7.03%       | 9.35%        | 6.85%       | 6.79%       |
| Jul   | 6.43%       | 7.17%       | 0.51%        | 7.11%       | 6.79%       |
| Aug   | 6.84%       | 5.82%       | 10.48%       | 7.65%       | 7.51%       |
| Sep   | 13.64%      | 16.58%      | 16.05%       | 12.54%      | 13.14%      |
| Oct   | 8.52%       | 6.87%       | 7.34%        | 8.39%       | 8.35%       |
| Nov   | 15.40%      | 15.85%      | 17.81%       | 14.95%      | 15.45%      |
| Dec   | 14.40%      | 14.53%      | 18.16%       | 14.49%      | 14.54%      |

---

## 2015 Annual Target Prediction

> Based on 2014 actual H2/H1 momentum × 10% base growth

| Metric    | 2014 Actual | Growth%  | 2015 Target |
|-----------|------------:|---------:|------------:|
| Sales     | $484,247    | +20.1%   | $581,484    |
| Profit    | $49,544     | +23.0%   | $60,937     |
| Customers | 923         | +18.7%   | 1,095       |
| Orders    | 969         | +19.2%   | 1,155       |
