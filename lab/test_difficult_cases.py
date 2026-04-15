from transform.cleaning_rules import clean_rows
from quality.expectations import run_expectations

def test_difficult_cases():
    # Mock data giả lập với các trường hợp khó
    raw_data = [
        # Trường hợp 1: effective_date ở tương lai
        {"doc_id": "policy_refund_v4", "chunk_text": "Hoàn tiền trong 14 ngày làm việc", "effective_date": "2026-12-31", "exported_at": "2026-04-14"},

        # Trường hợp 2: chunk_text chứa ký tự BOM và zero-width
        {"doc_id": "hr_leave_policy", "chunk_text": "\ufeff10 ngày phép năm\u200b", "effective_date": "2026-01-01", "exported_at": "2026-04-14"},

        # Trường hợp 3: doc_id không hợp lệ
        {"doc_id": "unknown_doc", "chunk_text": "Some random text", "effective_date": "2026-04-15", "exported_at": "2026-04-14"},

        # Trường hợp 4: effective_date không đúng định dạng
        {"doc_id": "sla_p1_2026", "chunk_text": "SLA text", "effective_date": "15/04/2026", "exported_at": "2026-04-14"},

        # Trường hợp 5: chunk_text quá ngắn
        {"doc_id": "it_helpdesk_faq", "chunk_text": "FAQ", "effective_date": "2026-04-15", "exported_at": "2026-04-14"},

        # Trường hợp 6: duplicate chunk_text
        {"doc_id": "policy_refund_v4", "chunk_text": "Hoàn tiền trong 7 ngày làm việc", "effective_date": "2026-04-15", "exported_at": "2026-04-14"},
        {"doc_id": "policy_refund_v4", "chunk_text": "Hoàn tiền trong 7 ngày làm việc", "effective_date": "2026-04-15", "exported_at": "2026-04-14"},

        # Trường hợp 7: effective_date đi lùi trong cùng doc_id
        {"doc_id": "policy_refund_v4", "chunk_text": "Hoàn tiền trong 7 ngày làm việc", "effective_date": "2026-04-15", "exported_at": "2026-04-14"},
        {"doc_id": "policy_refund_v4", "chunk_text": "Hoàn tiền trong 7 ngày làm việc", "effective_date": "2026-04-14", "exported_at": "2026-04-14"},
    ]

    # Áp dụng cleaning rules
    cleaned, quarantine = clean_rows(raw_data)

    # Kiểm tra expectation
    results, should_halt = run_expectations(cleaned)

    # In kết quả để kiểm tra
    print("Cleaned Rows:", cleaned)
    print("Quarantine Rows:", quarantine)
    for result in results:
        print(f"Expectation: {result.name}, Passed: {result.passed}, Detail: {result.detail}")

    # Đảm bảo không có expectation nào bị fail với severity \"halt\"
    assert not should_halt, "Pipeline should not halt due to failed expectations."

# Chạy test
if __name__ == "__main__":
    test_difficult_cases()