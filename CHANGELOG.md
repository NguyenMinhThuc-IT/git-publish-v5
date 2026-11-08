# Changelog

## 5.0.1 — Unreleased

- Windows: thêm setup.cmd, kiểm tra dependency và xin phép trước khi cài/nâng cấp qua winget.
- Dò nhiều Python qua py/registry/PATH, chạy probe, chọn và ghim executable tuyệt đối.
  Mục tiêu bản ổn định 3.11–3.15; ưu tiên 3.14 có bằng chứng Windows V5.0.0.
  Python 3.15 vẫn thử nghiệm, chưa công bố hỗ trợ khi chưa có CI PASS.
- Kiểm tra Git/gh bằng phiên bản và tính năng offline; không đặt trần phiên bản,
  không nâng cấp công cụ đang tương thích, không hạ cấp/gỡ hay tự đăng nhập GitHub.
- Cài mã nguồn vào LocalAppData, giữ các bản cũ/cấu hình, backup và rollback launcher.
  publish.cmd gọi script nội bộ với execution policy chỉ trong tiến trình con.
- Thêm test PowerShell mock dependency/winget, lỗi/từ chối/cài lại/Unicode/interpreter;
  mở rộng CI Windows 3.11–3.13 và lane thử nghiệm 3.15, giữ 10 cấu hình CI cũ.
- Giữ nguyên luồng publish, bảo vệ file nhạy cảm, Git history và xác nhận V5.

## 5.0.0 — Released

Theo kết quả đã công bố: 10/10 GitHub Actions jobs PASS; Windows đã publish thực tế.
Các ghi chú 5.0.0rc1 dưới đây là lịch sử audit trước phát hành.

## 5.0.0rc1 — Unreleased, audit bổ sung 2026-11-07

Không có tag hoặc GitHub Release. Đây là mã ứng viên tiếp tục QA.

### Sửa lỗi và bảo mật

- Chuẩn hóa origin HTTPS/SSH nhất quán; chặn owner/đích/push URL không đúng.
- Không coi lỗi mạng/quyền ngoài HTTP 404 là repository mới.
- Chặn root sai, detached HEAD và bare repo trước thao tác ghi.
- Quét đường dẫn index/lịch sử, kể cả file nhạy cảm đã xóa; pathspec literal,
  bảo vệ .gitignore symlink và giữ dữ liệu khi UTF-8 lỗi/quyền quét lỗi.
- Fast-forward không ghi đè ignored file; push thường vẫn reject khi remote đổi sau prepare.
- Nhận diện thêm thư mục và dotfile xác thực phổ biến.
- ZIP/matrix cùng allowlist và audit mẫu credentials; không in giá trị khớp.

### Kiểm thử và phân phối

- Test Git thật với remote local tạm; Unicode, cancel/EOF, lỗi subprocess,
  clipboard mock, installer và packaging.
- Bộ cài Windows có backup/rollback và User PATH, chưa xác minh native.
- Linux/macOS launcher ghim Python và bật UTF-8; Darwin được mô phỏng trên Ubuntu.
- Công cụ kiểm định ZIP/checksum, cú pháp và pytest từ nguồn giải nén tạm.
- Tài liệu cập nhật/gỡ cài, bảo mật, license options, blockers và release notes draft.

### Giới hạn

Windows/macOS thật, Linux containers, GUI và Python 3.10–3.13 còn thiếu môi trường.
Giấy phép/đích/phê duyệt phát hành chưa quyết định; giữ 5.0.0rc1, chưa stable.
