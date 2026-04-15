# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Hoàng Ngọc Anh  
**Vai trò:** Cleaning / Transformation  
**Ngày nộp:** 2026-04-15  
**Độ dài:** ~550 từ

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**
Tôi chịu trách nhiệm chính tại module `lab/transform/cleaning_rules.py`. Cụ thể, tôi đã thiết lập hệ thống rule mở rộng để đảm bảo dữ liệu "raw" từ crawl/export được chuẩn hóa tối đa trước khi đi vào vector database.

**Kết nối với thành viên khác:**
Tôi làm việc chặt chẽ với team Ingestion để xác định các pattern "lỗi" thường gặp trong file CSV export hạ tầng. Dữ liệu sau khi qua bộ lọc của tôi sẽ được team Embed sử dụng để upsert vào ChromaDB. Nếu tôi lọc quá gắt, team Embed sẽ thiếu dữ liệu; nếu tôi lọc lỏng, team Monitoring sẽ báo lỗi về chất lượng retrieval.

**Bằng chứng (commit / comment trong code):**
Trong file `cleaning_rules.py`, tôi đã triển khai 3 rule mới quan trọng:
- `RULE_NEW_1`: Unicode normalization (NFC) và loại bỏ whitespace "nguy hiểm" (BOM, zero-width space).
- `RULE_NEW_2`: Metadata consistency check dựa trên từ khóa theo từng `doc_id`.
- `RULE_NEW_3`: Kiểm tra tính đơn điệu (monotonicity) của `effective_date` để tránh tình trạng dữ liệu cũ ghi đè dữ liệu mới.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Một quyết định quan trọng của tôi là áp dụng chiến lược **"Quarantine over Halt"** cho lỗi metadata mismatch (`RULE_NEW_2`). 

Thay vì dừng toàn bộ pipeline khi phát hiện một chunk text không khớp với keywords của `doc_id` (ví dụ: một chunk về "mật khẩu" nhưng lại gán nhầm vào `hr_leave_policy`), tôi chọn đẩy record đó vào khu vực cách ly (Quarantine). 

**Lý do:** Trong môi trường production, dữ liệu rác từ upstream là hiển nhiên. Nếu chọn "Halt" (dừng pipeline), một record lỗi duy nhất có thể làm tê liệt toàn bộ luồng cập nhật kiến thức cho chatbot. Bằng cách đẩy vào Quarantine kèm lý do `doc_text_mismatch`, hệ thống vẫn tiếp tục xử lý các record sạch khác, trong khi team vận hành có thể tải file CSV quarantine về để debug và fix lỗi logic tại nguồn crawl mà không gây downtime cho system.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Trong quá trình chạy thử nghiệm với `run_id=rule3`, tôi đã phát hiện một anomaly nghiêm trọng về tính toàn vẹn của thời gian: **Dữ liệu đi lùi ngày (Non-monotonic Effective Date)**.

**Triệu chứng:** Trong file `quarantine_rule3.csv`, dòng số 7 ghi nhận một record của `hr_leave_policy` có `effective_date=2026-01-15` nhưng nó lại xuất hiện sau một record khác đã có ngày hiệu lực là `2026-03-01`.

**Phát hiện:** `RULE_NEW_3` của tôi đã so sánh `eff_norm` với `prev_eff` lưu trong `last_effective_by_doc`. Khi phát hiện `2026-01-15 < 2026-03-01`, rule này đã ngay lập tức chặn record đó lại.

**Fix:** Thay vì ghi đè dữ liệu cũ vào vector DB (làm sai lệch thông tin tư vấn cho user), record lỗi này bị đẩy vào quarantine với nguyên nhân `non_monotonic_effective_date`. Điều này giúp bảo vệ chatbot khỏi việc cung cấp các chính sách đã hết hạn.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Dưới đây là bằng chứng từ `run_id=rule3` trích xuất từ logs và quarantine:

- **Logs (`run_rule3.log`):**
  ```text
  run_id=rule3
  raw_records=19
  cleaned_records=11
  quarantine_records=8
  PIPELINE_OK
  ```

- **Quarantine CSV (`quarantine_rule3.csv`):**
  ```csv
  7,hr_leave_policy,Nhân viên dưới 3 năm...,2026-01-15,non_monotonic_effective_date,2026-01-15,2026-03-01
  ```
Việc lọc được 8 record rác (trong đó có lỗi lùi ngày và lỗi Unicode ẩn) đã giúp bộ chỉ mục (index) trong ChromaDB đạt độ tinh khiết 100% theo đúng contract.

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ tích hợp **LLM-based Semantic Validation** vào bước Transformation. Hiện tại `RULE_NEW_2` vẫn dùng keyword thô (hard-coded), dễ bị bỏ sót. Sử dụng một model nhỏ (như GPT-4o-mini hoặc Gemini Flash) để check "Sự phù hợp giữa nội dung và Doc ID" sẽ giúp phát hiện các lỗi logic tinh vi hơn mà Regex hay Keyword không thể xử lý.
