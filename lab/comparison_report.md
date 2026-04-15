# Báo cáo so sánh Evaluation Retrieval: Before và After Inject

Dưới đây là một bản tóm tắt tình trạng trước và sau khi thực thi inject dữ liệu xấu (\`inject-bad\`) vào ChromaDB.

## 1. Kết quả Before Inject
Tệp dữ liệu: \`artifacts/eval/before_inject_bad.csv\`
Đối với câu hỏi **q_refund_window**:
- \`contains_expected\`: yes
- \`hits_forbidden\`: **no**

## 2. Kết quả After Inject
Tệp dữ liệu: \`artifacts/eval/after_inject_bad.csv\`
Đối với câu hỏi **q_refund_window**:
- \`contains_expected\`: yes
- \`hits_forbidden\`: **yes**

## 3. Phân tích & Chứng minh
Mặc dù hệ thống vẫn tìm thấy chính sách dự kiến (\`contains_expected = yes\`), nhưng khi có lỗi tiêm dữ liệu xấu (inject-bad), hệ thống truy xuất (retrieval) bắt đầu trả về hoặc truy xuất trúng các bản ghi vi phạm hay dữ liệu lỗi hậu quả (*hits_forbidden* thay đổi từ **no** thành **yes**).

Điều này chứng minh khả năng Retrieval trở nên "tệ hơn" và nhiễu hơn đáng kể. Việc đưa rác vào (garbage in) đã khiến Retrieval kéo theo kết quả lỗi (garbage out), ảnh hưởng trực tiếp đến chất lượng của hệ thống hoặc vi phạm compliance (hit forbidden content).
