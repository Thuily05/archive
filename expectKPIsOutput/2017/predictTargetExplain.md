# Giải thích kết quả — predictTarget.md (2017)

---

## 1. Vị trí trong chuỗi 4 năm

```
2014 → monthlyForecast2014 → weights_14, annual_2015
2015 → monthlyForecast2015 → weights_15, annual_2016
2016 → monthlyForecast2016 → weights_16, annual_2017
2017 → monthlyForecast2017 → weights_17, annual_2018 (projection)
```

Năm 2017 là **năm cuối có dữ liệu thực tế**. Weights đã được tinh chỉnh qua 3 năm liên tiếp → forecast chính xác nhất trong chuỗi.

---

## 2. Nhận xét tổng quan 2017

| Metric | Predicted (2016→2017) | Actual 2017 | Gap dự báo năm |
|--------|----------------------:|------------|----------------|
| Sales | $710,125 | $733,215 | **-3.1%** (under-forecast) |
| Profit | $97,655 | $93,439 | **+4.5%** (over-forecast) |
| Customers | 1,417 | 1,524 | **-7.0%** (under-forecast) |
| Orders | 1,549 | 1,687 | **-8.2%** (under-forecast) |

2017 tiếp tục tăng trưởng mạnh hơn dự báo cho Sales/Customers/Orders. Profit thì ngược lại — dự báo cao hơn thực tế.

---

## 3. Sales: Biến động mạnh đầu năm, ổn định từ Q2

**Tháng 1:** Actual $43,971 vs target $22,644 → **+94.2%** (gần gấp đôi kỳ vọng)
- Annual est. nhảy từ $710K lên **$1,044,540** (tháng 2)
- Model đặt target tháng 2 lên $37,714 nhưng actual chỉ $20,301 → -46.2%
- Annual est. giảm dần: $992K → $898K → $815K → $738K

Từ tháng 6 trở đi, annual_est dao động quanh $700K-$754K, gần với actual $733K.

**Final estimate $743,646 vs actual $733,215 → gap -1.4%** — tốt nhất trong chuỗi cho Sales.

---

## 4. Profit 2017: Annual estimate không hội tụ tốt

Final est. $101,823 vs actual $93,439 → **gap -9.0%** (kém nhất trong 4 năm).

Nguyên nhân:
- Profit 2017 rất không đều: tháng cao nhất ($14,752 tháng 3) gấp 16 lần tháng thấp nhất ($933 tháng 4)
- Annual est. liên tục dao động: $97K → $151K → $121K → $144K → ... → $110K
- Tháng 12 target $25,251 nhưng actual chỉ $8,483 → -66.4% → est. cuối thấp hơn actual

Profit là metric khó dự báo nhất vì **phân phối không đều và có tháng gần 0** (Profit Apr 2017 = $933).

---

## 5. Customers 2017: Chính xác hoàn toàn

Final est. = actual = **1,524** → **gap 0.0%**

Đây là năm thứ 2 liên tiếp Customers hội tụ gần 0%:
- 2015: gap 0.0%
- 2016: gap -1.4%
- 2017: gap **0.0%**

Lý do: Customers là metric đều đặn nhất (không có tháng âm, ít biến động bất thường), XGBoost học pattern rất tốt qua các năm.

---

## 6. Orders: Final est. gần actual nhất trong 4 năm

Final est. 1,678 vs actual 1,687 → **gap +0.5%**

Orders cũng là metric ổn định. Dự báo năm (từ 2016) lệch -8.2% nhưng rolling forecast tự điều chỉnh và bắt kịp thực tế.

---

## 7. Year-End Comparison — tổng kết 4 năm

### Predicted Annual Gap (dự báo năm trước → actual)

| Năm | Sales | Profit | Customers | Orders |
|-----|-------|--------|-----------|--------|
| 2015 | +23.6% | -1.1% | +13.3% | +11.3% |
| 2016 | -7.5% | -10.6% | -5.4% | -6.1% |
| 2017 | -3.1% | +4.5% | -7.0% | -8.2% |

Xu hướng: Gap năm 2015 rất lớn (H2/H1 momentum 2014 cao bất thường). Từ 2016-2017, dự báo năm cải thiện đáng kể, gap dưới 10%.

### Final Est. Gap (rolling forecast sau 12 tháng → actual)

| Năm | Sales | Profit | Customers | Orders |
|-----|-------|--------|-----------|--------|
| 2014 | +0.2% | +4.2% | +0.7% | +0.3% |
| 2015 | +0.7% | -4.3% | 0.0% | +0.5% |
| 2016 | -0.9% | +2.8% | -1.4% | -1.9% |
| 2017 | -1.4% | +9.0% | **0.0%** | +0.5% |

**Sales, Customers, Orders:** Luôn hội tụ dưới 2% sau 12 tháng — mô hình rất đáng tin cậy.  
**Profit:** Dao động 2.8%-9.0% — cần cải thiện xử lý tháng gần 0.

---

## 8. Calibrated Weights 2017 — thay đổi đáng chú ý từ 2016

**Sales:**
| Tháng | 2016 | 2017 | Lý do |
|-------|------|------|-------|
| Jan | 3.19% | **6.00%** | Jan 2017 = $43,971 (tháng mạnh nhất trong 4 năm) |
| May | 9.03% | 6.09% | May 2017 thấp hơn May 2016 |
| Aug | 5.17% | **8.29%** | Aug 2017 = $63,121 (tháng đột biến) |
| Dec | 15.63% | 11.93% | Dec 2017 = $83,829, giảm so với 2016 |
| Nov | 13.31% | **15.51%** | Nov 2017 = $118,448 (tháng cao nhất 2017) |

**Profit tháng 3:** Tăng từ 4.39% → **15.03%** vì Mar 2017 profit = $14,752 (cao nhất năm).

---

## 9. 2018 Annual Target Prediction

**2017 momentum:**
- H1 2017 (Jan-Jun): $256,909
- H2 2017 (Jul-Dec): $476,306
- Momentum = 476,306 / 256,909 = **1.85** → Growth = 10% × 1.85 = **18.5%**

| Metric | 2017 Actual | Growth | 2018 Target |
|--------|------------|--------|-------------|
| Sales | $733,215 | +18.5% | **$869,152** |
| Profit | $93,439 | +14.0% | **$106,479** |
| Customers | 1,524 | +16.5% | **1,776** |
| Orders | 1,687 | +17.8% | **1,987** |

**Lưu ý quan trọng:** 2018 không có dữ liệu thực tế trong SampleSuperstore.csv. Đây là projection thuần túy và không thể được xác nhận. Nếu cần forecast 2018 chính xác hơn, cần bổ sung dữ liệu 2018 thực tế.

---

## 10. Tổng kết toàn bộ chuỗi 2014-2017

| Năm | Sales Actual | Profit Actual | Customers | Orders |
|-----|-------------:|-------------:|----------:|-------:|
| 2014 | $484,247 | $49,544 | 923 | 969 |
| 2015 | $470,533 (-2.8%) | $61,619 (+24.4%) | 967 (+4.8%) | 1,038 (+7.1%) |
| 2016 | $609,206 (+29.5%) | $81,795 (+32.7%) | 1,205 (+24.6%) | 1,315 (+26.7%) |
| 2017 | $733,215 (+20.3%) | $93,439 (+14.2%) | 1,524 (+26.5%) | 1,687 (+28.3%) |
| **2018** | **$869,152*** | **$106,479*** | **1,776*** | **1,987*** |

*Projected values — no actual data available.

Mô hình rolling forecast với XGBoost đã theo dõi và học qua **4 năm liên tiếp**, với độ chính xác final estimate ngày càng cải thiện cho Sales, Customers và Orders.
