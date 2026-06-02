# Storyboard — "Are We Going to Reach Our Goals?"

## 1. Mục tiêu của Dashboard

Dashboard được xây dựng để trả lời một câu hỏi kinh doanh cốt lõi:

> **Với đà tăng trưởng hiện tại, doanh nghiệp có đạt được KPI đã đặt ra không — và năm tới nên đặt mục tiêu ở mức nào?**

Cụ thể, dashboard hỗ trợ ba nhóm người dùng:
- **Management** — theo dõi hiệu suất thực tế so với KPI theo năm và tháng
- **Planning team** — tham chiếu tier range để đặt mục tiêu 2018 có cơ sở
- **Analyst** — xem chi tiết monthly forecast và annual estimate rolling

---

## 2. Story được chọn

**"Từ baseline đến moonshot — 4 năm đặt mục tiêu và kết quả thực tế (2014–2017) + dự phóng 2018"**

Hành trình narrative:

```
[Không có data] → Q1 thực tế 2014 → Baseline 2014 (XGBoost)
    → KPI được đặt → Kết quả thực tế → Tier đạt được
    → Lặp lại 2015, 2016, 2017
    → Dự phóng 2018 với 3 mức: Achievable / Challenging / Stretch
```

Điểm nhấn của story:
- 2014 đặc biệt vì **không có lịch sử** — baseline phải xây từ Q1 actual + seasonal weight
- Mỗi năm, KPI được đặt vào một tier cụ thể — dashboard cho thấy tier nào thực tế đạt được
- 2018 chưa có actual — dashboard đề xuất range thay vì một điểm duy nhất (trung thực về uncertainty)

---

## 3. Các lựa chọn hiển thị phản ánh story

| Tab | Chart | Lý do chọn |
|-----|-------|------------|
| **4-Year Overview** | Grouped bar: Baseline / KPI / Actual | So sánh 3 mốc cùng trục — thấy ngay năm nào vượt/miss KPI |
| | Color by tier | Tier color nhất quán xuyên suốt — xanh = tốt, đỏ = dưới baseline |
| | Achievement table | Số hóa tier, % vs KPI, % vs Baseline — lookup nhanh |
| **KPI Tier Ranges** | Stacked area bands | Thể hiện "vùng" tier — không phải ngưỡng cứng, mà là spectrum |
| | Bar overlay lên band | Actual nằm ở vùng nào trong spectrum — trực quan hơn bảng số |
| | Diamond markers 2018 | Gợi ý Achievable & Challenging cho 2018 — phân biệt rõ với actual |
| **Monthly Tracking** | Bar (green/red) + line target | Beat = xanh, miss = đỏ — decision ngay lập tức không cần đọc số |
| | Dual axis: annual estimate | Trục phụ rolling forecast — thấy xu hướng năm trong khi xem tháng |
| **2018 Projection** | Line actual + stacked range bar | Nối lịch sử vào tương lai — range bar thể hiện uncertainty thay vì false precision |
| | Metric cards | Baseline / Achievable / Challenging / Stretch side-by-side — so sánh nhanh 4 mức |

**Lựa chọn thiết kế nhất quán:**
- Cùng bảng màu tier xuyên suốt 4 tab (đỏ/xám/xanh dương/xanh lá/vàng/tím)
- `plotly` với `plot_bgcolor='rgba(0,0,0,0)'` — nền trong suốt, không cạnh tranh với data
- Selectbox metric/year: cho phép viewer tự khám phá thay vì bị ép theo một KPI

---

## 4. Ưu điểm

- **Narrative rõ ràng:** Title, tab order, và chart flow dẫn người xem từ "big picture" đến "chi tiết" đến "tương lai"
- **Tier system nhất quán:** Màu sắc không thay đổi giữa các tab — viewer học một lần, dùng xuyên suốt
- **Trung thực về uncertainty:** 2018 hiển thị range (Achievable → Stretch) thay vì một con số — tránh false confidence
- **Interactive:** Selectbox metric và year — một dashboard phục vụ được nhiều use case khác nhau
- **2014 baseline minh bạch:** Có expander giải thích cách tính từ Q1 actual — methodology không bị giấu

---

## 5. Nhược điểm

- **Thiếu narrative text trực tiếp trên dashboard:** Viewer phải tự suy ra story; không có caption dẫn dắt qua từng tab
- **2014 assumption bị giấu cuối trang:** Đây là điểm methodological quan trọng nhất nhưng nằm trong expander ở Tab 4 — dễ bị bỏ qua
- **Summary cards đầu trang cộng dồn 4 năm:** Tổng 2014–2017 không có nhiều ý nghĩa kinh doanh; dễ gây hiểu nhầm nếu không có context
- **Không có annotation cho outlier/turning point:** Ví dụ năm nào Sales tăng đột biến hoặc Profit sụt giảm — viewer phải tự tìm
- **Tier band ở Tab 2 dùng multiplier cố định:** `1.10 / 1.20 / 1.35` giống nhau cho tất cả metric — không phản ánh đặc thù của từng KPI

---

## 6. Có thể improve

| Khía cạnh | Cải thiện cụ thể |
|-----------|-----------------|
| **Narrative** | Thêm `st.info()` / `st.markdown()` 1-2 câu dẫn chuyện đầu mỗi tab |
| **Annotation** | Thêm `fig.add_annotation()` đánh dấu năm/tháng có biến động lớn |
| **2014 methodology** | Đưa Q1 projection note lên đầu Tab 2 hoặc Tab 1 thay vì giấu cuối Tab 4 |
| **Summary cards** | Đổi sang "best year" hoặc "latest year (2017)" thay vì tổng cộng dồn |
| **Tier multiplier** | Cho phép admin tùy chỉnh multiplier theo metric thay vì hardcode |
| **Mobile** | Layout `wide` hiện tại không responsive trên màn hình nhỏ — có thể thêm breakpoint |
| **Export** | Thêm nút download CSV / PNG cho từng chart để dùng trong slide/report |
