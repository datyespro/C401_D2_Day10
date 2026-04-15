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
| RULE_NEW_2: `doc_text_mismatch`          | `quarantine_records=4`     | `quarantine_records=4`     | Manifest cleanup-refund, detect sai doc_id + chunk content |
| Fix refund window prune (idempotency)    | `embed_prune_removed=0`    | `embed_prune_removed=1`    | Log cleanup-refund: stale chunk "14 ngày" removed from Chroma |

**Rule chính (baseline + mở rộng):**

- Fix stale refund time 14 -> 7
- Deduplication bỏ trùng
- Chuẩn hóa text BOM chars (Warn)
- Kiểm tra ngày tương lai (Halt)

**Ví dụ 1 lần expectation fail và cách xử lý:**
Khi dùng cờ `--no-refund-fix --skip-validate`, expectation `refund_no_stale_14d_window` sẽ bắt gặp violation=1 (chunk 14 ngày làm việc). Tuy nhiên pipeline đang override luồng `--skip-validate` nên chunk bẩn tiếp tục đi vào Chroma, giúp chúng ta thu nhận được `after_inject_bad.csv` minh họa sai số trong RAG Agent. Đội Observability sẽ detect qua fail logs và alert vào Kênh báo động.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent

### 3a. Vấn đề phát hiện (Grading iteration 1)

Từ **grading_run.py** trên run `ci-smoke2` phát hiện: `gq_d10_01` trả về `contains_expected=true` nhưng **`hits_forbidden=true`** ❌
- **Nguyên nhân:** Vector store Chroma vẫn chứa chunk cũ có text "14 ngày làm việc" trong top-k retrieval
- **Impact:** Mặc dù LLM agent nhìn thấy câu trả lời đúng (7 ngày), context vẫn chứa deprecated policy → **tiêu chí Merit không đạt**
- **Chứng cứ:** `artifacts/eval/grading_run.jsonl` trước fix (commit lịch sử)

### 3b. Fix & verification (cleanup-refund run)

**Giải pháp thực hiện:**
1. Rerun `python etl_pipeline.py run --run-id cleanup-refund`
   - Expectation `refund_no_stale_14d_window` PASS (violations=0)
   - Embed upsert idempotent: **`embed_prune_removed=1`** (xóa vector id cũ)
2. Regenerate grading: `python grading_run.py --out artifacts/eval/grading_run.jsonl`
3. Verify: `python instructor_quick_check.py --grading artifacts/eval/grading_run.jsonl`

**Kết quả định lượng:**

| Metric | Lần 1 (Before fix) | Lần 2 (After cleanup-refund) | Δ |
|--------|-------------------|------------------------------|---|
| `gq_d10_01: hits_forbidden` | ❌ `true` | ✅ `false` | **FIX** |
| `gq_d10_02: contains_expected` | ✅ `true` | ✅ `true` | - |
| `gq_d10_03: top1_doc_matches` | ✅ `true` | ✅ `true` | - |
| **Hạng nhóm** | ❌ Fail | ✅ **Merit** | **Achievement** |

**Chứng cứ:**
- Manifest trước/sau: `artifacts/manifests/manifest_ci-smoke2.json` vs `artifacts/manifests/manifest_cleanup-refund.json`
- Cleaned CSV: `artifacts/cleaned/cleaned_cleanup-refund.csv` (6 records, no stale refund)
- Grading final: `artifacts/eval/grading_run.jsonl` (all 3 criteria PASS)

### 3c. Kịch bản inject (Sprint 3 - chứng chỉ definition)
Loại bỏ thao tác fix `refund policy` từ rule Clean và bypass Expectation qua Command Sprint 3 (`--no-refund-fix --skip-validate`) nhằm tạo rác Database để so sánh eval before/after quality degradation.

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
