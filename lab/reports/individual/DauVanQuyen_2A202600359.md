# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Đậu Văn Quyền  
**Vai trò:** Quality / Expectations Owner  
**Ngày nộp:** 2026-04-15  
**Mã sinh viên:** 2A202600359

---

## 1. Tôi phụ trách phần nào?

**File / module:**

Tôi phụ trách mở rộng `lab/quality/expectations.py` và hoàn thiện báo cáo chất lượng `lab/docs/quality_report.md`. Module expectations là trái tim validation logic của pipeline — xác định quality gate giữa clean → embed.

**Kết nối với thành viên khác:**

- **Member 2** (Cleaning Rules Owner): Tôi trao đổi để kiểm chứng rule mới có tương thích với expectation mới (ví dụ, nếu rule nào normalize BOM, expectation của tôi sẽ detect nó).
- **Member 4** (Embed / Eval Owner): Nhờ chạy eval retrieval trước/sau inject để cấp evidence cho báo cáo quality.
- **Member 6** (Docs Owner): Gửi summary metric_impact và inject evidence để họ dùng trong group_report.

**Bằng chứ commitc:**

File `quality/expectations.py` được mở rộng từ 6 expectations baseline lên 8 expectations. Commit message ghi rõ: "Add E7 (BOM detection), E8 (future date validation)". Mỗi expectation có docstring comment giải thích mục tiêu và severity.

---

## 2. Một quyết định kỹ thuật

**Chọn severity: halt vs warn cho 2 expectation mới**

Tôi quyết định `chunk_text_no_bom_chars` dùng severity **warn** vì BOM/zero-width là anomaly hiếm gặp (dataset mẫu không có), nhưng nếu xuất hiện có thể gây confusion trong retrieval scoring. Ngược lại, `effective_date_not_future` dùng severity **halt** vì ngày hiệu lực từ tương lai là lỗi dữ liệu nghiêm trọng — không thể chấp nhận được để embed vào vector store production.

Quyết định này cân bằng giữa "phát hiện sớm" (warn) và "ngăn chặn xâm nhập" (halt). Dùng halt cho future date tránh scenario khó debug sau khi data bị embed sai.

---

## 3. Một lỗi hoặc anomaly đã xử lý

**Triệu chứng:** Khi chạy `python etl_pipeline.py run --no-refund-fix --skip-validate --run-id inject-bad`, tôi cần chứng minh rằng expectation có thể **phát hiện được** dữ liệu stale.

**Phát hiện:** Baseline expectation `refund_no_stale_14d_window` đã tồn tại nhưng tôi cần xác nhận nó hoạt động đúng. Chạy inject run, log cho thấy:

```
expectation[refund_no_stale_14d_window] FAIL (halt) :: violations=1
```

**Fix:** Không cần fix logic — expectation đã đúng. Điều tôi làm là **kiểm chứng** (verify) rằng nó phát hiện violation khi dữ liệu xấu được giữ lại. Output log chứng minh: `violations=1` chính là chunk policy_refund_v4 vẫn chứa "14 ngày làm việc".

Tôi ghi rõ lỗi này vào quality report: "Inject scenario proof: expectation fail when refund stale window not fixed."

---

## 4. Bằng chứng trước / sau

**Baseline run** (`run_id=2026-04-15T08-03Z`):

```
expectation[refund_no_stale_14d_window] OK (halt) :: violations=0
expectation[chunk_text_no_bom_chars] OK (warn) :: bom_chunks=0
expectation[effective_date_not_future] OK (halt) :: future_effective_dates=0
```

Tất cả expectation pass, pipeline exit 0. Dữ liệu "tốt" được chính thức embed.

**Inject run** (`run_id=inject-bad`):

```
expectation[refund_no_stale_14d_window] FAIL (halt) :: violations=1
expectation[chunk_text_no_bom_chars] OK (warn) :: bom_chunks=0
expectation[effective_date_not_future] OK (halt) :: future_effective_dates=0
WARN: expectation failed but --skip-validate → tiếp tục embed
```

Expectation refund fail (chứng minh phát hiện được sai lầm), nhưng pipeline vẫn tiếp tục vì `--skip-validate`. Kỹ thuật này cho phép ta demo dữ liệu xấu và so sánh retrieval (Sprint 3).

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi muốn tích hợp một expectation cho **doc_id_distribution_reasonable** — kiểm tra rằng không có nào trong 4 policy chính (policy_refund_v4, sla_p1_2026, it_helpdesk_faq, hr_leave_policy) bị mất hẳn sau clean. Điều này sẽ giúp phát hiện bug catalog hoặc quarantine quá aggressive. Cần định nghĩa "reasonable" trên dữ liệu thực và thêm unit test cho expectation mới.
