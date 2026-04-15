# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Anh Đức
**Vai trò:** Docs / Report Owner (Member 6)
**Ngày nộp:** 15/04/2026
**Độ dài yêu cầu:** 400–650 từ

---

## 1. Tôi phụ trách phần nào?

**File / module:**

- `contracts/data_contract.yaml` (Hoàn thiện team owner, rule channels, freshness measured)
- `docs/pipeline_architecture.md` (Minh họa pipeline bằng Mermaid.js)
- `reports/group_report.md` (Tổng hợp Data Report Metric cho nhóm)
- `README.md` (Bổ sung bộ script one-command line chạy End-to-end)

**Kết nối với thành viên khác:**

- Phối hợp với Nguyễn Thành Đạt (Member 1) để lấy logic Source Map và Failure mode cấu hình Contract Rules.
- Giao tiếp với Nguyễn Hoàng Việt (Member 5) lấy chỉ số Monitoring xây Runbook và mô tả Architecture.
- Lấy thông tin Log & Evaluate metrics Before/After Inject của Văn Quyên (Member 3) và Duy Linh (Member 4) ráp vào bài tổng luận nhóm.

**Bằng chứng:**
Tôi thực hiện gộp và biên tập bài viết của nhóm trên Markdown. Các minh họa Metric bao gồm `bom_chunks`, `eval` CSV cho hit_forbidden đều được cập nhật hoàn chỉnh. Commit message liên quan trực tiếp đến việc Document hóa Pipeline Architecture và RAG Evidence.

---

## 2. Một quyết định kỹ thuật

**Format tài liệu Mermaid.js cho System Architecture**
Thay vì thiết kế sơ đồ bằng Draw.io tĩnh (hình tĩnh chèn vào Markdown thường chậm cập nhật và khó search), tôi vẽ Topology trực tiếp vào `pipeline_architecture.md` dưới định dạng Mermaid DAG. Nhờ đó mọi thay đổi của Ingest Layer tới lúc Embed vào ChromaDB của anh em trong Team đều được thay đổi nhanh gọn trên code. Tài liệu đi liền với Data Flow.

---

## 3. Một lỗi hoặc anomaly đã xử lý

**Triệu chứng:**
Lúc review Draft Report cá nhân của nhóm làm Ingestion, member không lưu ý thông số File Size bị Drop từ Baseline CSV đẩy dội lại `quarantine_records` làm bảng Metric rỗng.

**Cách giải quyết:**
Tôi tự tra cứu Log Sprint 1 (Bản Run-id: 2026-04-15T08-03Z) và phát hiện ra cấu trúc của Dữ liệu. `raw_records` trả lại 10 hàng, nhưng Drop vào quarantine 4 dòng (do lỗi BOM và sai ngày). Cleaned đọng lại 6. Tôi ráp thông tin đó bù vào file Team Report một cách kịp thời và request Member 1 cập nhật Source SLA.

---

## 4. Bằng chứng trước / sau

Quá trình thu thập từ Log chứng minh quá trình hoàn thiện bài:
Trước Update, `README.md` mới đơn thuần là code Build Environtment rời rạc.
Sau Update, có Command tổng hợp cho người thao tác nhanh chỉ 1 câu lệnh Bash để sinh Artifacts và Manifest chuẩn cho Freshness API.

1 Dòng command thêm vào:

```bash
python etl_pipeline.py run && python etl_pipeline.py freshness --manifest artifacts/manifests/manifest_sprint1.json
```

---

## 5. Cải tiến tiếp theo

Nếu có thêm khoảng 2 giờ nữa, tôi sẽ cài đặt `MkDocs` Workflow cho Github Actions để chuyển toàn bộ file `.md` bài tập thành web Report tĩnh và thêm Dashboard View tổng hợp các lần run script hằng ngày. Việc đó gia tăng tính UI/UX Data Observability thay vì xem thông qua terminal.
