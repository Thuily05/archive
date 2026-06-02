# KPI Forecast & Target Planning — SampleSuperstore

> Dự án phân tích dữ liệu bán lẻ, xây dựng hệ thống dự báo KPI theo tháng bằng XGBoost,
> đặt mục tiêu hợp lý theo từng năm và theo dõi hiệu suất thực tế qua giao diện Streamlit.

---

## Ý tưởng tổng quan

Chúng tôi đang cố gắng trả lời câu hỏi:

> **"Are we going to reach our goals?"**

Thay vì đặt KPI cảm tính, hệ thống này:
1. Học pattern mùa vụ từ dữ liệu lịch sử bằng **XGBoost**
2. Dự báo target từng tháng theo chuỗi cuộn (rolling forecast)
3. So sánh actual vs target sau mỗi tháng, tự cập nhật trọng số
4. Gợi ý KPI hợp lý theo tier (Achievable / Challenging / Stretch)
5. Hiển thị toàn bộ trên dashboard Streamlit

---

## Dữ liệu đầu vào

| File | Mô tả |
|------|-------|
| `SampleSuperstore.csv` | Dataset bán lẻ 9.994 đơn hàng, 2014–2017, 4 metrics chính: Sales, Profit, Customers, Orders |

---

## Chuỗi Python chính — XGBoost Rolling Forecast

Các file chạy theo chuỗi kế thừa: mỗi năm nhận **calibrated weights** và **annual target** từ năm trước.

```
monthlyForecast2014.py
        ↓  (CALIBRATED_WEIGHTS, ANNUAL_TARGET_2015)
monthlyForecast2015.py
        ↓  (CALIBRATED_WEIGHTS, ANNUAL_TARGET_2016)
monthlyForecast2016.py
        ↓  (CALIBRATED_WEIGHTS, ANNUAL_TARGET_2017)
monthlyForecast2017.py
        ↓  (CALIBRATED_WEIGHTS, ANNUAL_TARGET_2018)
suggestTarget.py
```

### monthlyForecast2014.py
- **Input:** `SampleSuperstore.csv` + given Jan 2014 targets (Sales=$50K, Profit=$5K, Customers=50, Orders=100)
- **Logic:**
  - Dùng XGBoost học seasonal weights từ toàn bộ data (2014–2017) làm prior
  - 3 tháng đầu là giai đoạn thử nghiệm, target Jan được đặt thủ công
  - Sau mỗi tháng: so sánh actual vs target → cập nhật seasonal weights (alpha=0.30) và annual estimate (beta=0.50)
  - Cuối năm: retrain XGBoost trên actual 2014 → CALIBRATED_WEIGHTS
- **Output:** `CALIBRATED_WEIGHTS`, `ANNUAL_TARGET_2015`, `FORECAST_2014`, `ACTUAL_2014`

### monthlyForecast2015.py / 2016.py / 2017.py
- **Input:** CALIBRATED_WEIGHTS + ANNUAL_TARGET từ năm trước
- **Logic:** Giống 2014 nhưng không có given target — tất cả 12 tháng do model tự tính
- **Output:** Weights mới, annual target năm tiếp theo, forecast data

### suggestTarget.py
- **Input:** Import từ toàn bộ chain (monthlyForecast2014→2017)
- **Logic (Prospective):**
  - 2014: project annual từ Q1 actuals ÷ XGBoost seasonal weights (Q1 = 3 tháng thử nghiệm)
  - 2015–2017: dùng ANNUAL_TARGET từ năm trước làm baseline
  - Tính 4 tier ranges: Achievable (+10%), Challenging (+20%), Stretch (+35%), Moonshot (+50%)
- **Output:** `target/suggestTargetResult.md`, `target/suggestTargetChart.png`, `target/suggestTargetConst.py`

---

## Hyperparameters (dùng xuyên suốt)

| Tham số | Giá trị | Ý nghĩa |
|---------|---------|---------|
| `alpha` | 0.30 | Tốc độ cập nhật seasonal weights sau mỗi tháng actual |
| `beta` | 0.50 | Tốc độ cập nhật annual estimate (pace blending) |
| `BASE_GROWTH` | 10% | Tăng trưởng nền dùng để project annual năm tiếp theo |

---

## KPI Targets — `target/`

```
target/
├── target.py              # Human-set KPI targets (2014–2017), lựa chọn tier phù hợp
├── suggestTargetConst.py  # Auto-generated constants từ suggestTarget.py
├── suggestTargetResult.md # Bảng gợi ý KPI range dạng Markdown
└── suggestTargetChart.png # Chart tier bands 2014–2018
```

### target/target.py
KPI được con người đặt ra dựa trên gợi ý của model:

| Năm | Tier | Sales | Profit | Customers | Orders |
|-----|------|------:|-------:|----------:|-------:|
| 2014 | Challenging | $480K | $72K | 132 | 960 |
| 2015 | Achievable | $640K | $67K | 1,205 | 1,270 |
| 2016 | Challenging | $676K | $88K | 1,368 | 1,482 |
| 2017 | Challenging | $852K | $117K | 1,700 | 1,859 |

---

## Kết quả phân tích — `expectKPIsOutput/`

```
expectKPIsOutput/
├── 2014/
│   ├── predictTarget.md        # Bảng rolling forecast 12 tháng + calibrated weights + predict 2015
│   └── predictTargetExplain.md # Giải thích tiếng Việt toàn bộ kết quả và logic
├── 2015/
│   ├── predictTarget.md        # Như trên + Year-End Comparison (3 cột)
│   └── predictTargetExplain.md
├── 2016/
│   ├── predictTarget.md
│   └── predictTargetExplain.md
├── 2017/
│   ├── predictTarget.md        # Năm cuối có actual data + project 2018
│   └── predictTargetExplain.md
└── average/
    ├── goal_weights_Region.png         # Phân rã KPI target theo Region
    ├── goal_weights_Category.png       # Phân rã theo Category
    ├── goal_weights_Segment.png        # Phân rã theo Segment
    ├── goal_weights_Sub-Category.png   # Phân rã theo Sub-Category
    └── goal_weights_Region_x_Cat.png   # Phân rã Region × Category
```

Mỗi `predictTarget.md` gồm:
- **Q1 Projection detail** (cho 2014): cách suy ra annual baseline từ 3 tháng đầu
- **Rolling forecast table**: Target | Actual | Error% | Annual Estimate từng tháng
- **Year-End Comparison**: Predicted annual (năm trước) vs Sum monthly targets vs Final rolling estimate vs Actual
- **Calibrated Weights**: XGBoost weights sau khi retrain trên actual năm đó
- **Annual target prediction**: Dự báo cho năm tiếp theo

---

## Dashboard — `src/`

```
src/
├── app.py           # Streamlit app chính
└── requirements.txt # Dependencies
```

### Chạy app

```bash
# Cài dependencies (lần đầu)
pip install -r src/requirements.txt

# Chạy app
python -m streamlit run src/app.py
```

Mở browser: **http://localhost:8501**

### 4 tabs trong app

| Tab | Nội dung |
|-----|---------|
| 📊 4-Year Overview | Bar chart nhóm: Baseline vs KPI Target vs Actual theo từng năm. Bảng tier achievement. |
| 🎯 KPI Tier Ranges | Chart tier bands tương tác. Bảng gợi ý KPI range 2014–2018. |
| 📅 Monthly Tracking | Chọn năm + metric → bar chart target vs actual từng tháng (xanh = beat, đỏ = miss). Rolling annual estimate. |
| 🔭 2018 Projection | KPI cards Achievable/Challenging/Stretch. Progression chart 2014→2017 + 2018 range. |

---

## Modules sử dụng

| Module | Phiên bản | Dùng để |
|--------|-----------|---------|
| `xgboost` | ≥2.0 | Học seasonal weights từ monthly sales data |
| `pandas` | ≥2.0 | Aggregate data, xử lý time series |
| `numpy` | ≥1.26 | Tính toán cyclical features (sin/cos), weight normalization |
| `streamlit` | ≥1.35 | Dashboard UI |
| `plotly` | ≥5.20 | Interactive charts trong dashboard |
| `matplotlib` | ≥3.8 | Xuất static PNG charts (suggestTargetChart.png, average/*.png) |

---

## Luồng xử lý tổng thể

```
SampleSuperstore.csv
        │
        ▼
monthlyForecast2014.py   ──── Q1 actuals + XGBoost prior weights
        │
        │  CALIBRATED_WEIGHTS_14, ANNUAL_TARGET_2015
        ▼
monthlyForecast2015.py   ──── rolling forecast, compare actual vs target
        │
        │  CALIBRATED_WEIGHTS_15, ANNUAL_TARGET_2016
        ▼
monthlyForecast2016.py
        │
        │  CALIBRATED_WEIGHTS_16, ANNUAL_TARGET_2017
        ▼
monthlyForecast2017.py
        │
        │  CALIBRATED_WEIGHTS_17, ANNUAL_TARGET_2018
        ▼
suggestTarget.py  ─────────── tổng hợp, tính tier ranges, lưu output
        │
        ├── target/suggestTargetResult.md
        ├── target/suggestTargetChart.png
        └── target/suggestTargetConst.py
                │
                ▼
          target/target.py  ─── human sets KPI dựa trên gợi ý
                │
                ▼
          src/app.py  ──────── Streamlit dashboard
```

---

## Câu hỏi trung tâm

Toàn bộ hệ thống này được xây dựng để trả lời:

1. **KPI năm tới nên đặt ở mức nào là hợp lý?** → `suggestTarget.py` gợi ý range
2. **Tháng này chúng ta có đang đi đúng hướng không?** → `monthlyForecast*.py` so sánh actual vs target
3. **Cuối năm chúng ta có đạt goal không?** → Annual estimate tự converge sau 12 tháng
4. **Nhìn lại 4 năm, hiệu suất tổng thể thế nào?** → `src/app.py` dashboard
