# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Thành Đạt (2A202600203)
**Vai trò:** Ingestion Owner (Sprint 1)
**Ngày nộp:** 2026-04-15
**Độ dài yêu cầu:** **400–650 từ**

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `lab/docs/data_contract.md` — điền source map (3 nguồn), schema cleaned, quy tắc quarantine, canonical versions
- `lab/artifacts/logs/run_sprint1.log` — log pipeline sprint1
- `lab/artifacts/manifests/manifest_sprint1.json` — manifest sau khi chạy pipeline
- Tham gia `contracts/data_contract.yaml` — đồng bộ allowlist doc_id

**Kết nối với thành viên khác:**

- Phối hợp với **Cleaning Owner**: align 4 lý do quarantine trong contract (doc_id lạ, missing date, HR stale, dedup)
- Cung cấp `raw_records=10` làm baseline cho Cleaning Owner so sánh `cleaned_records` và `quarantine_records`
- Align với **Quality Owner**: schema trong contract phải khớp expectation `no_empty_doc_id`, `effective_date_iso_yyyy_mm_dd`

**Bằng chứng (commit / comment trong code):**

- Commit `066e550` — "[Sprint1] Ingestion Owner — data contract + pipeline sprint1 run"
- File `data_contract.md` có bảng source map 3 nguồn và quarantine rules

---

## 2. Một quyết định kỹ thuật (100–150 từ)

**Quyết định: Thứ tự debug theo pipeline — Freshness → Volume → Schema → Lineage**

Thay vì kiểm tra tất cả metric cùng lúc, tôi áp dụng thứ tự ưu tiên từ slide Day 10 (Phần D):

1. **Freshness** — kiểm tra `exported_at` trước tiên vì data cũ là nguyên nhân hàng đầu gây sai agent
2. **Volume** — `raw_records` vs `cleaned_records` delta cho biết có bao nhiêu dòng bị loại
3. **Schema** — allowlist `doc_id` là cổng chặn đầu tiên trước khi embed
4. **Lineage** — `run_id` gắn trên mọi artifact để trace nguồn gốc

Đây không phải quyết định về tool mà về **process suy luận** — giúp On-call không mò mẫm khi incident xảy ra.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

**Triệu chứng:** Sau khi chạy pipeline, `freshness_check=FAIL` trong log:

```
freshness_check=FAIL {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 117.884, "sla_hours": 24.0, "reason": "freshness_sla_exceeded"}
```

**Metric phát hiện:** `freshness_check` FAIL trong log, `age_hours=117.884 > sla_hours=24`

**Root cause:** File CSV mẫu có `exported_at = 2026-04-10`, hôm nay 2026-04-15 — đúng 117 giờ (hơn 5 ngày). Đây là **dữ liệu mẫu cố tình** để dạy cách xử lý stale data.

**Xử lý:** Không fix data mẫu mà ghi rõ trong `data_contract.md`: SLA đo ở boundary nào (`export` vs `publish`), và giải thích `age_hours` 117 là bình thường cho data snapshot chứ không phải lỗi pipeline.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Sprint 1 chỉ chạy pipeline chuẩn (không inject), so sánh trước/sau chưa áp dụng. Bằng chứng chính là log sprint1:

```
run_id=sprint1
raw_records=10
cleaned_records=6
quarantine_records=4
expectation[min_one_row] OK (halt) :: cleaned_rows=6
expectation[refund_no_stale_14d_window] OK (halt) :: violations=0
expectation[hr_leave_no_stale_10d_annual] OK (halt) :: violations=0
embed_upsert count=6 collection=day10_kb
PIPELINE_OK
```

Quarantine 4 dòng: duplicate (row 2 refund), missing date (row 5), HR stale (row 7, date 2025), unknown doc_id (row 9, legacy_catalog).

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ **mở rộng source map** thêm 2 nguồn: webhook real-time cho policy update và SFTP batch export từ HR system — mỗi nguồn bổ sung failure mode riêng (rate limit, partial sync, schema drift) để contract đầy đủ hơn cho On-call khi incident xảy ra.
