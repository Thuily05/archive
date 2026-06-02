# Giải thích kết quả — predictTarget.md (2014)

---

## 1. Mô hình là gì?

File `monthlyForecast2014.py` dùng **XGBoost + Adaptive Rolling Forecast** để dự báo target từng tháng của năm 2014. Thay vì đặt target cứng cho cả năm ngay từ đầu, mô hình **tự học và tự điều chỉnh** sau mỗi tháng khi có dữ liệu thực tế (actual).

---

## 2. Các thông số cấu hình

| Thông số | Giá trị | Ý nghĩa |
|----------|---------|---------|
| **alpha = 0.30** | 30% | Tốc độ cập nhật **trọng số mùa vụ** sau mỗi tháng. Nếu tháng này actual vượt target 20%, các tháng còn lại được điều chỉnh tăng 30% × 20% = 6%. |
| **beta = 0.50** | 50% | Tốc độ cập nhật **ước tính doanh thu cả năm**. Mỗi tháng, mô hình blend 50% ước tính cũ với 50% tốc độ thực tế hiện tại. |
| **base_growth = 10%** | 10% | Tốc độ tăng trưởng nền để dự đoán target năm 2015 từ actual 2014. |

---

## 3. Given January Target

Đây là target tháng 1/2014 được đặt thủ công từ đầu:

- Sales: **$50,000**
- Profit: **$5,000**
- Customers: **50**
- Orders: **100**

**Mục đích duy nhất:** Tính ra ước tính doanh thu cả năm ban đầu theo công thức:

> `Annual Est. ban đầu = Jan Target / trọng số XGBoost của tháng 1`

Ví dụ Sales: $50,000 / 3.89% = **$1,284,158** — con số này rất cao so với thực tế ($484,247) vì Jan target được đặt tham vọng. Tuy nhiên mô hình sẽ tự điều chỉnh dần sau mỗi tháng.

---

## 4. Các cột trong bảng Rolling Forecast

### Cột Target
Target của tháng đó, được tính theo công thức:

- **Tháng 1:** Lấy trực tiếp từ given target (xem mục 3).
- **Tháng 2–12:** `Target[m] = Ngân sách còn lại × w[m] / tổng(w[m..12])`
  - **Ngân sách còn lại** = Annual Est. hiện tại − tổng actual các tháng trước
  - **w[m]** = trọng số mùa vụ của tháng m (đã được cập nhật bởi alpha)

### Cột Actual
Doanh số thực tế từ file `SampleSuperstore.csv` của tháng đó. Đây là dữ liệu lịch sử, được dùng để đối chiếu và cập nhật mô hình — **không được dùng trước khi dự báo.**

### Cột Error%
Sai lệch giữa actual và target:

> `Error% = (Actual − Target) / |Target| × 100`

- **Dương (+):** Actual **vượt** target → tốt hơn kỳ vọng
- **Âm (−):** Actual **dưới** target → kém hơn kỳ vọng

### Cột Annual Est.
Ước tính doanh thu cả năm **tại thời điểm dự báo tháng đó** (trước khi cập nhật bằng actual tháng đó). Công thức cập nhật sau mỗi tháng:

> `Annual Est. mới = (1 − beta) × Annual Est. cũ + beta × Pace`  
> Trong đó: `Pace = Tổng actual đến hiện tại / Tổng trọng số mùa vụ đến hiện tại`

**Diễn giải:** Nếu Sales tháng 1–3 đạt $74,448 và tổng trọng số XGBoost của 3 tháng đó là 13.33%, thì Pace = $74,448 / 13.33% = $558,500 (tức là nếu tiếp tục tốc độ này cả năm, doanh thu sẽ đạt $558,500).

---

## 5. Tại sao Annual Est. hội tụ về gần thực tế?

| Metric | Annual Est. ban đầu | Annual Est. cuối năm | Actual | Sai lệch |
|--------|--------------------:|---------------------:|-------:|---------:|
| Sales | $1,284,158 | $483,174 | $484,247 | **+0.2%** |
| Customers | 1,378 | 917 | 923 | **+0.7%** |
| Orders | 2,908 | 966 | 969 | **+0.3%** |

Dù khởi đầu rất sai (do Jan target tham vọng), sau 12 tháng liên tục cập nhật theo actual, mô hình hội tụ đến sai lệch **dưới 1%** cho 3/4 metrics. Đây là điểm mạnh của Adaptive Rolling Forecast.

---

## 6. Calibrated Weights

Sau khi kết thúc 2014, XGBoost được **train lại từ đầu** trên dữ liệu actual 2014 thực tế (thay vì dùng prior từ tất cả các năm). Kết quả là bộ trọng số chính xác hơn cho từng tháng.

**Ví dụ Sales:**

| Tháng | Prior (tất cả năm) | Calibrated (chỉ 2014) | Thay đổi |
|-------|-------------------:|----------------------:|---------|
| Tháng 3 | 9.09% | 11.53% | Tăng — Mar 2014 mạnh hơn trung bình |
| Tháng 2 | 2.41% | 0.76% | Giảm — Feb 2014 rất thấp |
| Tháng 9 | 13.64% | 16.58% | Tăng — Sep 2014 là tháng cao nhất |

Bộ weights này được **export sang `monthlyForecast2015.py`** làm điểm xuất phát cho năm 2015.

**Profit Calibrated Weights** có một đặc điểm: tháng 7 chỉ 0.51% vì actual tháng 7/2014 là **-$841** (lỗ). XGBoost clip giá trị âm về 0, nên tháng 7 gần như không có trọng số trong profit.

---

## 7. 2015 Annual Target Prediction

Dự báo target cả năm 2015 dựa trên:

> `Annual 2015 = Actual 2014 × (1 + base_growth × momentum)`  
> Trong đó: `momentum = H2_2014 / H1_2014` (clamped từ 0.5 đến 2.5)

**H1 2014 (Jan–Jun):** Tổng actual tháng 1–6  
**H2 2014 (Jul–Dec):** Tổng actual tháng 7–12

Nếu H2 > H1 (kinh doanh tăng mạnh cuối năm), momentum > 1 → growth rate > 10%.

**Ví dụ Sales:**
- H1 = $160,986 | H2 = $323,261 | momentum = 2.0 (capped)
- Growth = 10% × 2.0 = **20%**
- 2015 Target = $484,247 × 1.20 = **$581,484**

---

## 8. Đọc kết quả như thế nào?

**Tháng có Error% dương lớn** (ví dụ Sep Sales +27.4%): Actual vượt kỳ vọng — dấu hiệu tốt, mô hình sẽ tự nâng target các tháng sau.

**Tháng có Error% âm lớn** (ví dụ Jan Sales -71.5%): Actual thấp hơn nhiều — do Jan target đặt quá cao so với thực tế. Mô hình nhanh chóng điều chỉnh lại từ tháng 2.

**Annual Est. giảm nhanh từ tháng 1 → tháng 5**: Phản ánh việc mô hình "học" rằng Jan target đặt quá tham vọng và đang hiệu chỉnh về mức thực tế.

**Annual Est. ổn định từ tháng 5 trở đi**: Khi đã có đủ actual data, ước tính năm hội tụ và chỉ dao động nhỏ xung quanh giá trị thực tế.

---

## 9. Output được dùng tiếp ở đâu?

| Export | Dùng cho |
|--------|----------|
| `CALIBRATED_WEIGHTS` | Trọng số ban đầu cho `monthlyForecast2015.py` |
| `XGB_MODELS` | Model XGBoost đã train trên 2014, dùng tiếp cho 2015 |
| `ANNUAL_TARGET_2015` | Target năm 2015 để khởi động rolling forecast 2015 |
| `ACTUAL_2014` | Dữ liệu so sánh và tham chiếu cho 2015 |
| `FORECAST_2014` | Lịch sử dự báo 2014 để phân tích độ chính xác |
