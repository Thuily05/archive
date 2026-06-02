# Giải thích kết quả — predictTarget.md (2016)

---

## 1. Chuỗi kế thừa đến 2016

```
2014 actuals → monthlyForecast2014 → CALIBRATED_WEIGHTS_14, ANNUAL_2015
                                            ↓
2015 actuals → monthlyForecast2015 → CALIBRATED_WEIGHTS_15, ANNUAL_2016
                                            ↓
2016 actuals → monthlyForecast2016 → CALIBRATED_WEIGHTS_16, ANNUAL_2017
```

Đến năm 2016, mô hình đã học qua **2 năm dữ liệu liên tiếp** (2014, 2015), nên weights ban đầu phản ánh tốt hơn xu hướng thực tế.

---

## 2. Nhận xét tổng quan 2016

| Metric | Annual target (2015→2016) | Actual 2016 | Gap dự báo năm |
|--------|------------------------:|------------|----------------|
| Sales | $563,628 | $609,206 | **-7.5%** (under-forecast) |
| Profit | $73,153 | $81,795 | **-10.6%** (under-forecast) |
| Customers | 1,140 | 1,205 | **-5.4%** (under-forecast) |
| Orders | 1,235 | 1,315 | **-6.1%** (under-forecast) |

2016 thực tế tăng trưởng mạnh hơn dự báo từ 2015 → tất cả 4 metrics đều vượt kế hoạch năm.

---

## 3. Vấn đề Profit tháng 1-3: Error bất thường

**Nguyên nhân gốc rễ:** Weights Profit tháng 1 từ 2015 chỉ 0.10% (gần 0) vì Jan 2015 bị lỗ, XGBoost đã học và assign weight gần 0 cho tháng 1.

Hệ quả trong 2016:
- Target Jan Profit = $73,153 × 0.10% = **$72** (rất thấp)
- Actual Jan Profit = **$2,825** → Error = +3,817%
- Ratio = 2,825/72 = 39.2 → bị cap về 5.0 (giới hạn an toàn)
- Annual est. nhảy lên **$1,469,647** (tháng 2)
- Dẫn đến target tháng 2 = $61,676 → actual chỉ $5,005 → Error = -91.9%

Từ tháng 4 trở đi, annual_est dần hồi phục về $73K-$80K và ổn định.

**Bài học:** Metric Profit cần xử lý riêng vì có tháng âm làm weights bị méo.

---

## 4. Sales: Annual estimate dao động nhưng hội tụ tốt

Annual est. Sales dao động trong năm:
- Tháng 1: $563,628 (initial)
- Tháng 2: $513,391 (Jan kém → giảm)
- Tháng 3: $581,893 (Feb tốt → tăng)
- Tháng 5: $604,782 (May tốt nhất +50.8% → đẩy lên)
- Tháng 7: $660,444 (cao nhất)
- Cuối năm: $614,960 (gần actual $609,206, gap **-0.9%**)

Dù dao động nhiều giữa năm, rolling forecast vẫn hội tụ về gần thực tế cuối năm.

---

## 5. Year-End Comparison — điểm nổi bật 2016

### Profit Sum Monthly = $315,343 vs Actual $81,795 (gap +285.5%)
Đây là hệ quả trực tiếp của vấn đề tháng 1-3. Khi annual_est Profit nhảy lên $1.47M (tháng 2), các target tháng sau rất cao ($61K, $125K...) dù actual chỉ vài nghìn. Tổng monthly targets bị thổi phồng nhưng không phản ánh forecast thực tế — chỉ final_est (sau khi hệ thống tự điều chỉnh) mới có ý nghĩa.

### Sales Final est. gap -0.9% — tốt nhất trong 3 năm
Nhờ có 2 năm dữ liệu học trước (2014, 2015), weights Sales đã được calibrate tốt hơn. Final est. $614,960 vs actual $609,206 — chỉ lệch dưới 1%.

---

## 6. Calibrated Weights — thay đổi đáng chú ý 2015→2016

**Sales:**
| Tháng | 2015 | 2016 | Lý do |
|-------|------|------|-------|
| May | 6.24% | **9.03%** | May 2016 có $56,988 — tháng cao nhất |
| Oct | 7.00% | **9.82%** | Oct 2016 tốt ($59K vs $31K năm 2015) |
| Nov | 16.06% | **13.31%** | Nov 2016 thấp hơn kỳ vọng ($79K vs $75K) |

**Profit:**
- Oct 2016 = **19.02%** (cao nhất) do $16,243 trong tháng 10
- Dec 2016 = **20.33%** do $17,885 trong tháng 12
- Tháng 1 từ 0.10% → **3.49%** vì Jan 2016 profit dương ($2,825)

---

## 7. 2017 Annual Target Prediction

**2016 momentum:**
- H1 2016 (Jan-Jun): $229,320
- H2 2016 (Jul-Dec): $379,886
- Momentum = 379,886 / 229,320 = **1.66** → Growth = 10% × 1.66 = **16.6%**

| Metric | 2016 Actual | Growth | 2017 Target |
|--------|------------|--------|-------------|
| Sales | $609,206 | +16.6% | **$710,125** |
| Profit | $81,795 | +19.4% | **$97,655** |
| Customers | 1,205 | +17.6% | **1,417** |
| Orders | 1,315 | +17.8% | **1,549** |

---

## 8. Tổng kết độ chính xác Final Est. qua các năm

| Năm | Sales gap | Profit gap | Customers gap | Orders gap |
|-----|-----------|-----------|--------------|-----------|
| 2014 | +0.2% | +4.2% | +0.7% | +0.3% |
| 2015 | +0.7% | -4.3% | **0.0%** | +0.5% |
| 2016 | **-0.9%** | +2.8% | -1.4% | -1.9% |

Sales và Customers/Orders luôn hội tụ dưới 2% sau 12 tháng. Profit dao động nhiều hơn do có tháng âm làm mất ổn định trọng số ban đầu.
