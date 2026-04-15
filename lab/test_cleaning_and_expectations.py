from transform.cleaning_rules import clean_rows
from quality.expectations import run_expectations

def test_cleaning_and_expectations():
    # Mock data giả lập
    raw_data = [
        {"doc_id": "policy_refund_v4", "chunk_text": "14 ngày làm việc", "effective_date": "2026-04-15", "exported_at": "2026-04-14"},
        {"doc_id": "hr_leave_policy", "chunk_text": "10 ngày phép năm", "effective_date": "2025-12-31", "exported_at": "2026-04-14"},
        {"doc_id": "unknown_doc", "chunk_text": "Some text", "effective_date": "2026-04-15", "exported_at": "2026-04-14"},
        {"doc_id": "sla_p1_2026", "chunk_text": "SLA text", "effective_date": "2026-04-15", "exported_at": "2026-04-14"},
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

    # Đảm bảo không có expectation nào bị fail với severity "halt"
    assert not should_halt, "Pipeline should not halt due to failed expectations."

# Chạy test
if __name__ == "__main__":
    test_cleaning_and_expectations()