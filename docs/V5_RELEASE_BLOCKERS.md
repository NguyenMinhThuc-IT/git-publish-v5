# V5 release blockers — 5.0.0rc1

Ngày kiểm chứng: 2026-11-07. Chỉ phát hành sau phê duyệt chủ dự án.

## Phân loại

- P0: ảnh hưởng nghiêm trọng diện rộng, phải dừng phát hành.
- P1: nguy cơ mất dữ liệu/lộ thông tin hoặc gate bắt buộc chưa đủ bằng chứng.
- P2: chất lượng, trải nghiệm, tài liệu hoặc phạm vi hỗ trợ cần theo dõi.

## Audit đang xác minh

| ID | Mức | Vấn đề | Trạng thái / hành động |
|---|---|---|---|
| SEC-01 | P1 | Fast-forward có thể ghi đè file local bị ignore | FIXED / PASS: --no-overwrite-ignore, file/HEAD được giữ nguyên |
| SEC-02 | P1 | Matrix có policy copy nguồn riêng, có thể mang credentials.py vào container | FIXED / PASS: dùng chung allowlist với ZIP |
| SEC-03 | P1 | Scanner thiếu thư mục/.dotfile xác thực phổ biến | FIXED / PASS: .aws/.ssh/.gnupg/.netrc/.npmrc/.pypirc |
| DIST-01 | P2 | Thiếu blockers, changelog, hướng dẫn update/uninstall, release notes draft | FIXED / PASS: đã thêm và kiểm tra link/docs |
| QA-01 | P2 | Thiếu verifier release tái sử dụng | FIXED / PASS: checksum, manifest, compile, pytest và lỗi recovery |

P0: chưa phát hiện trong phạm vi đã kiểm tra; không phải chứng nhận toàn bộ an toàn.

## Gate ngoài môi trường/quyền phiên

| ID | Gate | Trạng thái | Điều kiện giải quyết |
|---|---|---|---|
| GATE-01 | Giấy phép / quyền phân phối | NOT TESTED / chưa quyết định | Chủ dự án chọn, xác nhận quyền và điền LICENSE |
| GATE-02 | Windows PS 5.1/7 + CMD | NOT TESTED | Windows/runtime thật; test PATH/backup/rollback/clipboard |
| GATE-03 | macOS/Bash 3.2/Zsh/pbcopy | NOT TESTED | macOS/runtime thật |
| GATE-04 | Sáu Linux containers | SKIPPED | Docker/Podman có sẵn và đủ quyền; không tự cài |
| GATE-05 | Python 3.10–3.13 | NOT TESTED | Interpreter thật hoặc môi trường được phép |
| GATE-06 | Ubuntu Server riêng / GUI clipboard | NOT TESTED | Host/GUI tương ứng |
| GATE-07 | GitHub thật | NOT TESTED | Phê duyệt repository thử và thao tác mạng có ghi |
| GATE-08 | Đích phát hành và phê duyệt công khai | NOT TESTED / chưa phê duyệt | Chủ dự án quyết định; giữ nguyên origin hi |
| GATE-09 | Review bí mật nhúng trong source | NOT TESTED toàn diện | Audit tự động chỉ kiểm tra mẫu biết trước; cần duyệt trước chia sẻ |

Không hạ phiên bản xuống stable hoặc coi runtime thiếu là PASS.

## Điểm tiếp tục cho phiên sau

- P0 kỹ thuật: 0 phát hiện; P1/P2 đã phát hiện ở bảng audit: 0 còn mở.
- Kết quả: 170 passed, 0 failed, 5 skipped; 8 failures trước sửa đã được xử lý.
- Candidate mới: dist/git-publish-5.0.0rc1-audit2.zip; manifest/report ngoài ZIP.
- GATE-01…09 vẫn cần quyết định hoặc môi trường mới, không được tự đổi thành PASS.
- Không lặp audit/viết lại các phần đã đạt; khi có runtime, chỉ chạy kiểm tra tương ứng
  và regression liên quan, rồi cập nhật báo cáo và tạo artifact tên mới.
