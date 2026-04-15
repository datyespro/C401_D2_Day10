# Quality report — Lab Day 10

**run_id:** 2026-04-15T08-03Z  
**Ngày:** 2026-04-15

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước | Sau | Ghi chú |
|--------|-------|-----|---------|
| raw_records | 10 | 10 | cùng file raw |
| cleaned_records | 6 | 6 | vẫn giữ 6 record sạch |
| quarantine_records | 4 | 4 | unchanged for baseline and inject run |
| Expectation halt? | no | yes for inject, but skipped validate | baseline pass, inject fail warning |

---

## 2. Before / after retrieval (bắt buộc)

> Chưa có file eval retrieval chạy trực tiếp tại thời điểm này. Nếu có, sẽ đính kèm `artifacts/eval/before_after_eval.csv` và `artifacts/eval/after_inject_bad.csv`.

**Câu hỏi then chốt:** refund window (`q_refund_window`)  
**Trước:** expectation `refund_no_stale_14d_window` OK với baseline.  
**Sau:** expectation `refund_no_stale_14d_window` FAIL trong scenario `inject-bad` khi dùng `--no-refund-fix`, ghi rõ violation=1.

**Merit (khuyến nghị):** versioning HR — `q_leave_version`  
**Trước:** expectation `hr_leave_no_stale_10d_annual` OK trong baseline.  
**Sau:** chưa có evidence retrieval cho `q_leave_version` tại thời điểm này.

---

## 3. Freshness & monitor

> Kết quả `freshness_check` từ run baseline: FAIL.

- `latest_exported_at`: `2026-04-10T08:00:00`
- `age_hours`: 120.066
- `sla_hours`: 24.0
- `reason`: `freshness_sla_exceeded`

Giải thích: dữ liệu mẫu hiện tại cũ hơn SLA 24 giờ, nên pipeline báo FAIL freshness mặc dù các expectation clean/pass vẫn OK. Để pass, cần cập nhật snapshot raw hoặc điều chỉnh SLA hợp lý trong `FRESHNESS_SLA_HOURS`.

---

## 4. Corruption inject (Sprint 3)

> Mô tả: Chạy `python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate` để giữ dữ liệu refund stale và so sánh.

- Mục tiêu inject: giữ lại policy refund với cửa sổ 14 ngày và chứng minh expectation `refund_no_stale_14d_window` fail.
- Kết quả: expectation `refund_no_stale_14d_window` FAIL (violations=1).
- Vì dùng `--skip-validate`, pipeline vẫn tiếp tục embed và kết thúc với `PIPELINE_OK`, nhưng log có cảnh báo: `WARN: expectation failed but --skip-validate → tiếp tục embed`.

---

## 5. Hạn chế & việc chưa làm

- Chưa có file eval retrieval actual; cần chạy `python eval_retrieval.py --out artifacts/eval/before_after_eval.csv` và `python eval_retrieval.py --out artifacts/eval/after_inject_bad.csv` để bổ sung evidence before/after.
- Chưa có bằng chứng `q_leave_version` trong retrieval; cần thêm test cho HR versioning nếu muốn đạt Merit tốt hơn.
- Freshness hiện FAIL do dữ liệu mẫu cũ; cần giải thích rõ trong runbook và/hoặc cập nhật SLA.
