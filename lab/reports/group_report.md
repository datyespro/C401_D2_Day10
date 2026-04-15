# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** C401-D2  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Nguyễn Thành Đạt | Ingestion / Raw Owner | nguyenthanhdat0512.work@gmail.com |
| Hoàng Ngọc Anh | Cleaning & Quality Owner | hoanganh24704@gmail.com |
| Đậu Văn Quyền | Quality / Expectations Owner | quyendvpa00242@gmail.com |
| Vũ Duy Linh | Embed & Idempotency Owner | vuduylinh150804@gmail.com |
| Nguyễn Hoàng Việt | Monitoring / Docs Owner | nguyenhoangviet23022004@gmail.com |
| Nguyễn Anh Đức | Docs & Report Owner | nguyenanhduc2909@gmail.com |

**Ngày nộp:** 15/04/2026  
**Repo:** [github.com/datyespro/C401_D2_Day10](https://github.com/datyespro/C401_D2_Day10)

---

## 1. Pipeline tổng quan

Luồng khai thác dữ liệu bẩn từ export `policy_export_dirty.csv`. Quá trình Ingestion lấy vào, sau đó gửi qua tầng Clean (xóa BOM, format date). Tầng Quality dùng Expectations để Halt hoặc Warn với các files sai chuẩn (vi phạm sẽ đá file sang thư mục Quarantine). Sau cùng dữ liệu chuẩn được Embed Idempotent (upsert ghi đè theo `chunk_id`) vào collection `day10_kb` qua ChromaDB. Đi kèm luồng là `manifest` và `run_id` được ghi chú vết lại ở mỗi bước chạy phục vụ monitoring.

**Lệnh chạy một dòng (End-to-end pipeline):**

```bash
python etl_pipeline.py run && python etl_pipeline.py freshness --manifest artifacts/manifests/manifest_sprint1.json
```

---

## 2. Cleaning & expectation

### 2a. Bảng metric_impact

| Rule / Expectation mới (tên ngắn)        | Trước (số liệu)            | Sau / khi inject (số liệu) | Chứng cứ (log / CSV / commit)         |
| ---------------------------------------- | -------------------------- | -------------------------- | ------------------------------------- |
| Expectation: `chunk_text_no_bom_chars`   | `bom_chunks=0`             | `bom_chunks=0` (warn)      | Log baseline run_id=2026-04-15T08-03Z |
| Expectation: `effective_date_not_future` | `future_effective_dates=0` | `future_effective_dates=0` | Log baseline run_id=2026-04-15T08-03Z |

**Rule chính (baseline + mở rộng):**

- Fix stale refund time 14 -> 7
- Deduplication bỏ trùng
- Chuẩn hóa text BOM chars (Warn)
- Kiểm tra ngày tương lai (Halt)

**Ví dụ 1 lần expectation fail và cách xử lý:**
Khi dùng cờ `--no-refund-fix --skip-validate`, expectation `refund_no_stale_14d_window` sẽ bắt gặp violation=1 (chunk 14 ngày làm việc). Tuy nhiên pipeline đang override luồng `--skip-validate` nên chunk bẩn tiếp tục đi vào Chroma, giúp chúng ta thu nhận được `after_inject_bad.csv` minh họa sai số trong RAG Agent. Đội Observability sẽ detect qua fail logs và alert vào Kênh báo động.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent

**Kịch bản inject:**
Loại bỏ thao tác fix `refund policy` từ rule Clean và bypass Expectation qua Command Sprint 3 nhằm tạo rác Database.

**Kết quả định lượng:**

- Evaluated cho `q_refund_window`:
- Lần 1 Pipeline (Before): `hits_forbidden` trả ra **no**, Agent không bị ảnh hưởng do Vector DB đã lưu `chunk_text` đúng 7 ngày.
- Lần 2 Inject (After): Rác bị inject làm `hits_forbidden` thay thành **yes**, Agent trả lời sai "14 ngày làm việc". Rõ ràng Observability pipeline có tác động bảo vệ chất lượng RAG rất lớn!

---

## 4. Freshness & monitoring

Freshness setup SLA giới hạn ở mức 24h đo tại Publish pipeline. Tuy nhiên do dataset csv raw có snapshot cũ (file có timestamp export_at ~ hơn 117h), pipeline bắn `FAIL` cho `freshness_check`. Cảnh báo này chỉ là sai lệch Snapshot do lab, nhưng minh chứng cho tính nhạy của Watermark metrics và clock-skew trên production.

---

## 5. Liên hệ Day 09

Dữ liệu hoàn thiện ở Labeling và Dedupe Day 10 được nhúng riêng sang `day10_kb`. Mảng Multi-agent Day 09 sẽ được cập nhật route context sang Data VectorStore mới này để đạt tính chính xác policy (như nhân sự, hoàn tiền Helpdesk) chuẩn nhất.

---

## 6. Rủi ro còn lại & việc chưa làm

- Metric Pruning DB khi vector hết hạn theo timeline chưa được phát triển.
- Expectation phân bổ file/tài liệu bị phân vùng chưa triệt để.
