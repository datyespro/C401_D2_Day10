# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| `policy_export_dirty.csv` (manual export) | CSV file read via `load_raw_csv()` | Duplicate rows (2 dòng trùng refund), missing `effective_date`, stale policy version, unknown `doc_id` | `raw_records` vs `cleaned_records` delta; `quarantine_records` count |
| `data/docs/*.txt` (source docs) | 4 file chuẩn: policy_refund_v4, sla_p1_2026, it_helpdesk_faq, hr_leave_policy | Chunk boundary sai (heading-based), stale refund 14→7 ngày, HR version conflict (10 vs 12 ngày phép) | `exported_at` timestamp; `effective_date` ISO format check |
| CMS/HR system (giả định) | Export CSV batch | Ngày không chuẩn (DMY `01/02/2026`), `doc_id` lạ (`legacy_catalog_xyz_zzz`) không thuộc allowlist | Schema validation fail; quarantine_reason per record |

> **Thứ tự debug theo pipeline:**
> `Freshness (exported_at) → Volume (raw_records) → Schema (allowlist doc_id) → Lineage (run_id)`

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | Hash ổn định: `{doc_id}_{seq}_{sha256_16chars}` |
| doc_id | string | Có | Thuộc allowlist: policy_refund_v4, sla_p1_2026, it_helpdesk_faq, hr_leave_policy |
| chunk_text | string | Có | Min 8 ký tự; chuẩn hoá whitespace; fix stale refund 14→7 |
| effective_date | date (YYYY-MM-DD) | Có | Quarantine nếu rỗng hoặc không parse được ISO |
| exported_at | datetime | Có | UTC timestamp; dùng đo freshness SLA |

---

## 3. Quy tắc quarantine vs drop

| Tình huống | Xử lý | Ai approve |
|-----------|-------|-----------|
| `doc_id` không thuộc allowlist | Quarantine → `quarantine_[run_id].csv` | Data Engineer |
| `effective_date` rỗng hoặc không parse ISO | Quarantine | Data Engineer |
| HR policy effective_date < 2026-01-01 (bản cũ) | Quarantine | HR SME |
| `chunk_text` rỗng | Quarantine | Data Engineer |
| `chunk_text` trùng (dedup) | Quarantine | Data Engineer |

> **Không silent-drop** — mọi loại trừ đều có lý do ghi trong `reason` field của quarantine CSV.

---

## 4. Phiên bản & canonical

| Document | Canonical source | Version hiện tại | Stale marker |
|----------|-----------------|-----------------|--------------|
| Policy Refund | `data/docs/policy_refund_v4.txt` | v4 (2026-02-01) | `14 ngày làm việc` → fix thành `7 ngày làm việc` |
| SLA P1 | `data/docs/sla_p1_2026.txt` | 2026 | — |
| IT Helpdesk FAQ | `data/docs/it_helpdesk_faq.txt` | 2026 | — |
| HR Leave Policy | `data/docs/hr_leave_policy.txt` | 2026 (12 ngày phép) | Bản 2025 có `10 ngày phép` → quarantine |

**Run ID convention:** `YYYY-MM-DDTHH-MMZ` (UTC) hoặc custom string (vd `inject-bad`, `sprint1`)
