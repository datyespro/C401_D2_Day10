# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Hoàng Việt  
**Vai trò:**  Monitoring
**Ngày nộp:** 15/04/2026
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**
- Tôi phụ trách file 'monitoring/freshness_check.py', 'docs/runbook.md'.


**Kết nối với thành viên khác:**

- Tôi đã phối hợp với các thành viên khác để xác định các metric cần thiết cho việc phát hiện sự cố và xây dựng runbook chi tiết để xử lý sự cố khi phát hiện ra.

**Bằng chứng (commit / comment trong code):**
- coment trong file freshness_check.py


---

## 2. Một quyết định kỹ thuật (100–150 từ)

> VD: chọn halt vs warn, chiến lược idempotency, cách đo freshness, format quarantine.

- Thêm watermark lag metric để đo độ trễ giữa dữ liệu nguồn và dữ liệu đã được xử lý. Điều này giúp phát hiện sớm các vấn đề về độ trễ trong pipeline và đảm bảo rằng dữ liệu luôn được cập nhật kịp thời.
- Thêm clock skew metric để đo sự khác biệt về thời gian giữa các thành phần trong pipeline. Điều này giúp phát hiện và xử lý các vấn đề liên quan đến đồng bộ hóa thời gian, đảm bảo rằng tất cả các thành phần hoạt động đồng bộ và dữ liệu được xử lý chính xác.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

> Mô tả triệu chứng → metric/check nào phát hiện → fix.

- Triệu chứng: Khi inject policy_export_dirty, agent retrieve chunk có chứa nội dung "Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc kể từ xác nhận đơn " Trong khi đó số ngày thực tế là 7 ngày làm việc. Điều này có thể dẫn đến việc agent đưa ra câu trả lời sai.
- Metric phát hiện: eval 'hit_forbidens'
- Fix: tạm banner “data stale”

---

## 4. Bằng chứng trước / sau (80–120 từ)

> Dán ngắn 2 dòng từ `before_after_eval.csv` hoặc tương đương; ghi rõ `run_id`.
question_id,question,top1_doc_id,top1_preview,contains_expected,hits_forbidden,top1_doc_expected,top_k_used
q_refund_window,Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi xác nhận đơn?,policy_refund_v4,Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng.,no,yes,,3

hits_forbidden đã chuyển từ 'yes' sang 'no' sau khi fix, cho thấy rằng chunk chứa thông tin sai đã được loại bỏ khỏi kết quả truy vấn, giúp cải thiện độ chính xác của câu trả lời mà agent đưa ra.

---

## 5. Cải tiến tiếp theo (40–80 từ)

> Nếu có thêm 2 giờ — một việc cụ thể (không chung chung).

- Thêm alert tự động khi phát hiện data stale dựa trên watermark lag, giúp giảm thời gian phản hồi và xử lý sự cố nhanh hơn.
- Xây dựng dashboard để theo dõi các metric freshness và clock skew theo thời gian thực