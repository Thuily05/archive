# Tools — XGBoost & Streamlit

Hai công cụ chính được sử dụng trong dự án này.

---

## XGBoost

### XGBoost là gì?

**XGBoost** (Extreme Gradient Boosting) là một thuật toán machine learning thuộc họ **Gradient Boosted Trees** — xây dựng một ensemble gồm nhiều cây quyết định nhỏ, mỗi cây học từ sai số của cây trước.

```
Dự đoán cuối = cây_1 + cây_2 + cây_3 + ... + cây_n
               (mỗi cây sửa lỗi của tổng các cây trước)
```

### Tại sao dùng XGBoost ở đây?

Trong dự án này, XGBoost **không dùng để dự báo doanh số trực tiếp**, mà dùng để **học seasonal weights** — tức là tỷ trọng đóng góp của từng tháng vào tổng năm.

Ví dụ, nếu model học được rằng tháng 11–12 chiếm ~25% doanh số năm, thì:
- Biết annual target → chia ngược ra target từng tháng
- Sau khi có actual → so sánh, cập nhật weights

```
Input features (mỗi tháng):
  - month_sin, month_cos      (cyclical encoding)
  - quarter                   (1–4)
  - is_holiday_season         (Q4 flag)
  - lag_1, lag_3              (giá trị tháng trước)

Output:
  - seasonal_weight[month]    (tỷ trọng tháng đó trong năm)
```

### Rolling Forecast — cách XGBoost được dùng theo thời gian

```
Đầu năm:
  weights = XGBoost weights từ năm trước (prior)

Sau tháng M:
  new_weight[M] = (1 - alpha) × predicted_weight[M]
                + alpha       × (actual[M] / annual_estimate)
  → annual_estimate được cập nhật (blending với beta)

Cuối năm:
  retrain XGBoost trên actual năm đó → CALIBRATED_WEIGHTS
  → truyền sang năm tiếp theo
```

Nhờ vòng lặp này, model ngày càng khớp với pattern thực tế của doanh nghiệp.

### Hyperparameters liên quan

| Tham số | Giá trị | Vai trò |
|---------|---------|---------|
| `alpha` | 0.30 | Tốc độ cập nhật weights sau mỗi tháng — cao hơn = bám actual nhanh hơn nhưng dễ overfit noise |
| `beta` | 0.50 | Tốc độ cập nhật annual estimate — cân bằng giữa forecast ban đầu và pace thực tế |
| `n_estimators` | 200 | Số cây trong XGBoost |
| `max_depth` | 3 | Độ sâu tối đa mỗi cây — giữ thấp để tránh overfit trên dataset nhỏ (12 điểm/năm) |

### Lưu ý về dataset nhỏ

Dữ liệu chỉ có **12 điểm mỗi năm** (1 điểm = 1 tháng). XGBoost thường cần nhiều dữ liệu hơn để phát huy, nhưng ở đây nó chủ yếu dùng như một **weighted regression** để học seasonal pattern — không kỳ vọng generalization cao mà kỳ vọng tính nhất quán của pattern mùa vụ.

---

## Streamlit

### Streamlit là gì?

**Streamlit** là một Python framework để xây dựng web app và dashboard **chỉ bằng Python thuần** — không cần HTML, CSS, hay JavaScript.

```python
import streamlit as st

st.title("Hello World")
st.line_chart([1, 2, 3, 4])
```

Chạy `streamlit run app.py` → có ngay web app tại `localhost:8501`.

### Cách Streamlit hoạt động

Mỗi khi người dùng tương tác (chọn dropdown, click button), Streamlit **re-run toàn bộ script từ đầu**. State được giữ qua `st.session_state`.

```
User tương tác
      │
      ▼
Script chạy lại từ đầu
      │
      ▼
st.cache_resource / st.cache_data → bỏ qua các phần đã cache
      │
      ▼
Render lại UI với giá trị mới
```

### Các thành phần dùng trong dự án

| Component | Dùng ở đâu | Mục đích |
|-----------|-----------|---------|
| `st.set_page_config()` | Đầu app | Đặt title, icon, layout wide |
| `st.cache_resource` | `load()` | Cache toàn bộ data chain — chỉ load 1 lần |
| `st.tabs()` | Layout chính | Chia 4 tab: Overview / Tier / Monthly / Projection |
| `st.columns()` | Summary cards, tab layout | Chia cột ngang |
| `st.selectbox()` | Mỗi tab | Chọn metric / năm |
| `st.metric()` | Tab 1, Tab 4 | Hiển thị số lớn kèm delta |
| `st.plotly_chart()` | Mỗi tab | Nhúng Plotly figure tương tác |
| `st.dataframe()` | Mỗi tab | Bảng có style (color by tier) |
| `st.expander()` | Tab 4 | Ẩn/hiện chi tiết 2014 Q1 methodology |

### Tại sao chọn Streamlit thay vì Dash hay Tableau?

| Tiêu chí | Streamlit | Dash | Tableau |
|---------|-----------|------|---------|
| Ngôn ngữ | Python thuần | Python + callback | Drag & drop |
| Setup | `pip install` + 1 file | Nhiều file hơn | Cài riêng |
| Phù hợp | Prototype, data project | Production app | Business BI |
| Tích hợp ML | Tự nhiên (cùng Python) | Được nhưng verbose | Hạn chế |
| Chi phí | Miễn phí | Miễn phí (core) | Tốn phí bản đầy đủ |

Streamlit phù hợp với dự án này vì toàn bộ logic đã viết bằng Python — dashboard chỉ là một lớp hiển thị thêm vào, không cần tách stack.

### Cache — điểm quan trọng nhất

```python
@st.cache_resource(show_spinner="Loading forecast chain 2014→2017 ...")
def load():
    # Import toàn bộ chain — chạy 1 lần duy nhất
    from monthlyForecast2014 import ...
    from monthlyForecast2015 import ...
    ...
```

Không có `@st.cache_resource`, mỗi lần chọn dropdown sẽ re-import và tính lại toàn bộ chain — chậm vài giây mỗi lần tương tác.

---

## Kết hợp hai công cụ trong dự án

```
XGBoost (offline)                    Streamlit (online)
─────────────────                    ──────────────────
Học seasonal weights          →      Hiển thị kết quả
Tính tier ranges              →      Cho phép filter theo metric/năm
Dự báo annual target 2018     →      Vẽ progression chart + range bar
Rolling forecast 12 tháng     →      Bar chart xanh/đỏ từng tháng
```

XGBoost xử lý toàn bộ logic phân tích offline (các file `monthlyForecast*.py`, `suggestTarget.py`). Streamlit chỉ đọc kết quả đã tính và render — không có ML nào chạy trong lúc người dùng tương tác với dashboard.
