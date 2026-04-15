# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

> User / agent thấy gì? Khi inject policy_export_dirty, agent retrieve chunk có chứa nội dung "Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc kể từ xác nhận đơn " Trong khi đó số ngày thực tế là 7 ngày làm việc. Điều này có thể dẫn đến việc agent đưa ra câu trả lời sai.

---

## Detection

> Metric nào báo? eval 'hit_forbidens'

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Kiểm tra `artifacts/manifests/*.json` | quarantine records = 5 |
| 2 | Mở `artifacts/quarantine/*.csv` |Có chunk "Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc kể từ xác nhận đơn" |
| 3 | Chạy `python eval_retrieval.py` | hit_forbiden = 'no' |

---

## Mitigation

> Rerun pipeline, rollback embed, tạm banner “data stale”

---

## Prevention

> Thêm expectation, alert, owner, watermark lag, clockskew
