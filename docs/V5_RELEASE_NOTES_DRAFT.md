# Git Publish 5.0.0rc1 — release notes DRAFT

**BẢN NHÁP NỘI BỘ — CHƯA PHÊ DUYỆT XUẤT BẢN.** Không tạo tag, không upload
GitHub Release và không thay visibility trong phiên này.

## Nội dung ứng viên

CLI Python chuẩn bị Git/GitHub publish có preview, xác nhận commit, Private mặc định,
kiểm tra remote/visibility/lịch sử và bảo vệ file nhạy cảm theo đường dẫn.
Bổ sung chống ghi đè ignored file khi fast-forward, nhận diện thư mục xác thực,
thống nhất policy staging/ZIP và audit credentials mẫu biết trước.

## Cài đặt và nâng cấp

Cần Python >=3.10, Git và gh có sẵn. Không tự cài dependency hệ thống.
Xem [hướng dẫn cài/cập nhật/gỡ](V5_INSTALL_UPDATE_UNINSTALL.md),
[Quick Start](../README.md), [changelog](../CHANGELOG.md) và [bảo mật](V5_SECURITY.md).
Giữ source cũ cho tới khi xác minh launcher mới; không trộn source hai phiên bản.

## Bằng chứng và phạm vi

Kết quả mới nhất ở [báo cáo kiểm định](V5_FINAL_REPORT.md) và manifest ngoài ZIP
trong dist. Chỉ xác nhận các test offline trên Ubuntu hiện tại và các trường hợp
mô phỏng được ghi rõ. Không công bố Windows/macOS/container là hỗ trợ chính thức.
Checksum/manifest xác minh dữ liệu artifact; source không phải binary đóng gói.

## Known issues và gate

Xem [blockers](V5_RELEASE_BLOCKERS.md). LICENSE chưa được chọn; quyền phân phối,
đích phát hành và phê duyệt công khai đang chờ chủ dự án. Native Windows/macOS,
container Linux, GUI và Python 3.10–3.13 cần QA bổ sung.

## Mẫu tài sản phát hành để duyệt

- ZIP nguồn ứng viên có SOURCE_MANIFEST.json.
- SHA-256 sidecar và release-manifest JSON (version, checksum, kết quả kiểm định, gates).
- Release notes này và tài liệu cài đặt/bảo mật.

Chỉ thay DRAFT bằng trạng thái phát hành và gắn phiên bản stable sau khi tất cả
gate áp dụng được chấp thuận. Không ghi URL download công khai khi chưa xuất bản.
