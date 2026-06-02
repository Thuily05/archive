# Giải thích kết quả — predictTarget.md (2015)

---

## 1. Điểm khác biệt chính so với 2014

| Điểm | 2014 | 2015 |
|------|------|------|
| Điểm khởi đầu | Given Jan target thủ công | Lấy từ output của `monthlyForecast2014` |
| Tháng 1 target | Cố định = $50,000 | Tự tính từ model (XGBoost weight × annual) |
| Annual target ban đầu | Suy ra từ Jan target / w[Jan] | Trực tiếp = ANNUAL_TARGET_2015 từ 2014 |
| Weights ban đầu | Prior từ tất cả các năm | CALIBRATED_WEIGHTS từ 2014 actuals |
| Phần so sánh cuối năm | Không có | **Có thêm Year-End Comparison** |

---

## 2. Chuỗi dữ liệu từ 2014 sang 2015

```
monthlyForecast2014.py
  └── CALIBRATED_WEIGHTS   → weights ban đầu cho tháng 1/2015
  └── ANNUAL_TARGET_2015   → ngân sách năm cho rolling forecast 2015
        ↓
monthlyForecast2015.py
  └── CALIBRATED_WEIGHTS   → weights ban đầu cho 2016
  └── ANNUAL_TARGET_2016   → ngân sách năm cho rolling forecast 2016
```

Mỗi năm **kế thừa trạng thái đã học** từ năm trước, không phải bắt đầu lại từ đầu.

---

## 3. Cách tính Target tháng 1/2015

Vì không có given target, tháng 1 được tính giống các tháng còn lại:

> `Target[Jan] = Annual_Est × w[Jan] / sum(w[Jan..Dec])`  
> `= $581,484 × 3.04% / 100% = $17,680`

Đây là trọng số w[Jan] = 3.04% được lấy từ **CALIBRATED_WEIGHTS** của 2014.

---

## 4. Diễn giải cột Annual Est. trong bảng

Cột này hiển thị ước tính doanh thu cả năm **tại thời điểm bắt đầu tháng đó** (trước khi thấy actual). Công thức cập nhật sau mỗi tháng:

> `Annual Est. mới = 0.5 × Annual Est. cũ + 0.5 × Pace`  
> `Pace = Tổng actual đến hiện tại / Tổng trọng số XGBoost đến hiện tại`

**Ví dụ Sales tháng 2:**
- Sau Jan: actual = $18,174, w[Jan] = 3.04%
- Pace = $18,174 / 3.04% = $597,829
- Annual Est. = 0.5 × $581,484 + 0.5 × $597,829 = **$589,611**

**Ví dụ Sales tháng 3:**
- Sau Feb: thực actual Feb vượt target rất nhiều (+166.9%)
- Model điều chỉnh tăng: Annual Est. = **$691,177** (tháng 2 thực tế tốt → kỳ vọng cả năm tăng)

Sau tháng 3 actual (-51.1%), estimate giảm nhanh về $570K rồi dần converge về ~$467K.

---

## 5. Vấn đề Profit: Tháng 2-3 có target bất thường

**Nguyên nhân:** Tháng 1/2015 actual profit = **-$3,281** (lỗ). Điều này xảy ra vì:
- Error ratio = -3,281 / 3,034 = **-1.08** (âm) → ratio bị clip về 0.10
- Annual Est. sau Jan = (1-0.5) × 60,937 + 0.5 × (-3,281/4.98%) = $30,468 + (-32,949) = **-$2,481**

Khi annual_est âm, remaining_budget cũng âm → target tháng 2 ra $13, tháng 3 ra -$48.

Tuy nhiên từ tháng 4 trở đi, khi có nhiều actual dương, annual_est hồi phục về $59K-$82K và forecast trở lại bình thường. Đây là **giới hạn của mô hình** khi profit có tháng âm.

**Giải pháp cho tương lai:** Tách riêng model Profit, dùng absolute value cho pace calculation.

---

## 6. Year-End Comparison — đọc như thế nào?

Bảng so sánh 3 loại dự báo với actual:

### Cột 1: Predicted annual (2014 output)
Dự báo được tính từ năm 2014, **trước khi năm 2015 bắt đầu**. Đây là kế hoạch năm.

- Sales lệch **+23.6%**: 2014 có H2/H1 momentum = 2.0 (rất cao), nên dự báo tăng trưởng 20%. Thực tế 2015 tăng trưởng thấp hơn.
- Profit lệch **-1.1%**: Gần như chính xác hoàn toàn.
- Customers lệch **+13.3%**, Orders lệch **+11.3%**: Overestimate nhẹ.

### Cột 2: Sum monthly (rolling)
Tổng cộng tất cả target từng tháng trong năm. Con số này **không bằng annual target** vì mỗi tháng target được tính lại dựa trên remaining budget (đã trừ các actual trước đó).

- Nếu thực tế liên tục **dưới** target → remaining budget ngày càng lớn → target tháng sau cao → tổng monthly > actual
- Sales: $521,900 vs actual $470,533 → tổng target 10.9% cao hơn actual (model kỳ vọng nhiều hơn thực tế)

### Cột 3: Final est. (sau 12 tháng)
Ước tính annual sau khi cập nhật qua 12 tháng actual. Đây là con số **chính xác nhất** vì đã học từ tất cả dữ liệu.

| Metric | Final est. gap |
|--------|--------------|
| Sales | **+0.7%** — gần như chính xác |
| Profit | **+4.3%** — kém hơn do tháng âm |
| Customers | **0.0%** — chính xác tuyệt đối |
| Orders | **+0.5%** — gần như chính xác |

---

## 7. Calibrated Weights — thay đổi từ 2014 sang 2015

**Sales:**
| Tháng | 2014 | 2015 | Lý do |
|-------|------|------|-------|
| Jan | 3.04% | 4.00% | Jan 2015 ($18K) mạnh hơn so với năm trước |
| Mar | 11.53% | 8.26% | Mar 2015 ($38K) yếu hơn Mar 2014 ($55K) |
| Aug | 5.82% | 7.92% | Aug 2015 ($36K) mạnh hơn Aug 2014 ($27K) |
| Sep | 16.58% | 13.44% | Sep 2015 ($64K) thấp hơn Sep 2014 ($81K) |

**Profit tháng 1:** Chỉ 0.10% (gần như 0) vì Jan 2015 profit âm → XGBoost clip về 0.

---

## 8. 2016 Annual Target Prediction

Công thức giống 2014→2015:
> `Annual 2016 = Actual 2015 × (1 + 10% × momentum_2015)`

**2015 momentum:**
- H1 2015 (Jan-Jun) Sales: ~$157K
- H2 2015 (Jul-Dec) Sales: ~$313K  
- Momentum = 313/157 = **2.0** (capped) → Growth = 10% × 2.0 = **19.8%**

| Metric | 2015 Actual | Growth | 2016 Target |
|--------|------------|--------|-------------|
| Sales | $470,533 | +19.8% | $563,628 |
| Profit | $61,619 | +18.7% | $73,153 |
| Customers | 967 | +17.9% | 1,140 |
| Orders | 1,038 | +19.0% | 1,235 |

---

## 9. Kết luận về độ chính xác

| Metric | Năm 2014 final gap | Năm 2015 final gap |
|--------|-------------------|-------------------|
| Sales | +0.2% | +0.7% |
| Profit | +4.2% | -4.3% (bị ảnh hưởng bởi tháng âm) |
| Customers | +0.7% | **0.0%** |
| Orders | +0.3% | +0.5% |

Mô hình rolling adaptive với alpha=0.30, beta=0.50 **hội tụ rất tốt** sau 12 tháng cho Sales, Customers, Orders. Profit cần xử lý đặc biệt cho các tháng có giá trị âm.

---

## 10. Output được dùng tiếp ở đâu?

| Export | Dùng cho |
|--------|----------|
| `CALIBRATED_WEIGHTS` | Trọng số ban đầu cho `monthlyForecast2016.py` |
| `XGB_MODELS` | Model XGBoost đã train trên 2015 actuals |
| `ANNUAL_TARGET_2016` | Target năm 2016 ($563K Sales, $73K Profit...) |
| `ACTUAL_2015` | Dữ liệu so sánh và tham chiếu cho 2016 |
| `FORECAST_2015` | Lịch sử dự báo 2015 để phân tích |
