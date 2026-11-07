# Git Publish V5 — release checklist

Phiên bản ứng viên: 5.0.0rc1. Không phát hành tự động từ checklist này.

## Đã kiểm tra trong phiên

- [x] Baseline và regression offline trên Ubuntu.
- [x] Git local tạm: remote mismatch, phân nhánh, fast-forward, rejected push.
- [x] Detached HEAD, Unicode/dấu cách, hủy/EOF, visibility và timeout mô phỏng.
- [x] File nhạy cảm trong index/lịch sử, kể cả đã xóa; ignore/pathspec literal.
- [x] Rà soát bộ cài Linux/macOS/Windows; backup và lỗi installer.
- [x] ZIP allowlist, symlink/cache/credentials fixtures và manifest/hash.
- [x] Tài liệu phân biệt PASS, FAIL, SKIPPED, NOT TESTED.
- [x] Giữ nguyên Git HEAD/index/origin; không tạo repo hay push GitHub.
- [x] Audit2: regression fast-forward giữ ignored file và remote đổi sau prepare.
- [x] Audit2: matrix/ZIP dùng chung allowlist và chặn mẫu credentials nội dung.
- [x] Audit2: verifier checksum/manifest/compile/pytest từ nguồn giải nén tạm.
- [x] Hướng dẫn cập nhật/gỡ, bảo mật, CHANGELOG và release notes DRAFT.
- [x] Có tài liệu license options để chủ dự án quyết định, LICENSE giữ nguyên.
- [x] Có bảng P0/P1/P2 và gate trong V5_RELEASE_BLOCKERS.md.

## Cần trước khi phát hành công khai

- [ ] Chủ dự án quyết định và điền LICENSE (hiện trống).
- [ ] Xác định đích phát hành riêng; origin workspace hiện là hi, không tự thay.
- [ ] Thử Windows thật: PS 5.1/7, CMD, py/python, Unicode, PATH, backup/rollback.
- [ ] Thử macOS thật: Bash 3.2, Zsh, Python/Git/gh, pbcopy, PATH.
- [ ] Chạy container Ubuntu 24/26, Debian, Fedora, Arch, Kali; lưu log/digest.
- [ ] Thử Ubuntu Server riêng và GUI Wayland/X11/Desktop.
- [ ] Chạy Python 3.10–3.13 thật; parse grammar 3.10 chưa thay thế runtime test.
- [ ] Kiểm định GitHub thật bằng repository thử được chủ dự án cho phép,
      gồm lỗi xác thực/quyền, visibility và push; chưa được phép trong phiên này.
- [ ] Rà soát thủ công secrets nhúng trong source/documentation trước chia sẻ ZIP.
- [ ] Đối chiếu SHA-256/manifest với bản source đã duyệt.
- [ ] Phê duyệt phát hành và version final; không bỏ hậu tố rc trước khi đủ bằng chứng.

## Giới hạn được giữ rõ

Quét theo tên/đường dẫn không thay thế secret scanner nội dung.
Không làm sạch lịch sử hoặc thu hồi credentials tự động.
Không auto-merge lịch sử phân nhánh, không force push, không đổi origin.
Manifest đảm bảo toàn vẹn, không chứng nhận ZIP không chứa mọi loại bí mật.
Giấy phép và phát hành công khai cần quyết định của chủ dự án.

## Kết quả audit2 — 2026-11-07

170 passed / 0 failed / 5 skipped trên Ubuntu; ZIP kiểm định tạm cũng đạt
170 passed / 5 skipped. Kết quả từ chính ZIP bàn giao ghi trong dist/verify-audit2.json.
Giữ 5.0.0rc1, chưa RELEASE READY cho công khai; các checkbox còn mở ở trên là gate.
