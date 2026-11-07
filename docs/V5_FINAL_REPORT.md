# Git Publish V5 — báo cáo kiểm định hiện tại

Phiên bản **5.0.0rc1**, vòng **audit2**, ngày **2026-11-07**, Asia/Ho_Chi_Minh.

## Trạng thái phát hành

**RELEASE CANDIDATE — BLOCKED FOR PUBLIC RELEASE.**
Đã hoàn thành phần kỹ thuật được phép trong môi trường hiện tại; chưa chuyển stable,
chưa phát hành, chưa chọn license hoặc repository đích. Giữ nguyên origin hi.

PASS = kiểm tra đã chạy và đạt đúng phạm vi; FAIL = kiểm tra đã chạy còn lỗi;
SKIPPED = bài kiểm tra bị bỏ qua do môi trường; NOT TESTED = chưa có bằng chứng
native/dịch vụ hoặc gate chưa được quyết định. Review/mock không thay native test.

## Kết quả kiểm chứng

| Hạng mục | Kết quả hiện tại | Phạm vi |
|---|---|---|
| Baseline phiên tiếp tục | PASS: 146 passed, 5 skipped, 3.24s | Chạy trước sửa, khớp phiên trước |
| Pytest workspace sau audit2 | PASS: 170 passed, 5 skipped, 3.76s | 175 collected, 0 failures/errors |
| Pytest từ ZIP kiểm định tạm | PASS: 170 passed, 5 skipped | Công cụ verify_release, Git config/gh credentials được cô lập |
| Lỗi P0/P1 kỹ thuật còn mở | FAIL: 0 trong phạm vi đã kiểm tra | Không chứng nhận không có lỗi ngoài phạm vi |
| Cú pháp Python | PASS: 32 file | Compile Python 3.14.4, parse grammar 3.10; không ghi pyc |
| Cú pháp Bash | PASS | install.sh, install-macos.sh; Bash 5.3.9 |
| Cú pháp PowerShell/Zsh | SKIPPED | Không có powershell/pwsh/zsh |
| Git integration thật | PASS | Bare remote tạm; không có GitHub push |
| Source ZIP và checksum | PASS kiểm định | 50 source files + SOURCE_MANIFEST.json, CRC/SHA-256/roundtrip |
| Audit credentials nội dung | PASS với mẫu biết trước | 50 source files được phép, không in giá trị khớp |
| Linux containers | SKIPPED, 6 môi trường | Không có Docker/Podman; không khởi chạy container |
| Git metadata dự án | PASS đối chiếu hash | HEAD/index/config/refs không thay đổi |
| LICENSE | NOT TESTED / chưa quyết định | Vẫn trống; không áp dụng license nào |

Năm skipped của pytest: PowerShell 5.1 parser, pwsh parser, hai bài cài/chạy trên
Windows và cú pháp PATH bằng Zsh. Sáu container SKIPPED được ghi riêng, không cộng
vào 5 skipped của pytest. NOT TESTED chưa có số lượng test case hữu hạn để cộng;
xem chín nhóm gate trong [blockers](V5_RELEASE_BLOCKERS.md).

Môi trường chạy: Ubuntu 26.04.1 LTS, Python 3.14.4, pytest 9.0.2, Git 2.53.0,
gh 2.46.0. Thiếu Docker/Podman/PowerShell/Zsh và Python 3.10–3.13 trong PATH.

## Những việc mới, không lặp lại phần đã đạt

| ID | Mức | Trước sửa | Bản sửa và bằng chứng |
|---|---|---|---|
| SEC-01 | P1 | Fast-forward mặc định có thể ghi đè ignored file local | --no-overwrite-ignore; regression giữ nguyên file/HEAD |
| SEC-02 | P1 | Matrix copy nguồn riêng, mang credentials.py vào container | Dùng chung allowlist/audit của ZIP; regression không copy file |
| SEC-03 | P1 | Thiếu tên thư mục/dotfile xác thực phổ biến | .aws/.ssh/.gnupg/.netrc/.npmrc/.pypirc, gồm lịch sử đã xóa |
| DIST-01 | P2 | Thiếu tài liệu bàn giao/phân phối | Bổ sung blockers, update/uninstall, security, license options, changelog, release notes draft |
| QA-01 | P2 | Chưa có verifier tái sử dụng cho candidate | Checksum/manifest/compile/extracted pytest; timeout, thiếu JUnit, lỗi hoặc toàn skip đều FAIL |

Regression trước sửa tái hiện 8 failures bằng dữ liệu giả, không dùng credentials
thật. Sau sửa lõi: 155 passed, 5 skipped. Thêm content audit: 159 passed, 5 skipped.
Verifier và tests ban đầu: 166 passed, 5 skipped. Vòng cuối: 170 passed, 5 skipped.
Không xóa/làm yếu test để đạt xanh; các failures nêu trên đã được xử lý trong mã.

Bổ sung kiểm thử remote thay đổi sau prepare: push thường bị reject, lịch sử
remote/local giữ nguyên. Không retry bằng force push hoặc reset.

## Những phần đã giữ nguyên và kiểm tra hồi quy

- Origin HTTPS/SSH, tài khoản đích, fetch/push URL, repository đã tồn tại và visibility.
- Không commit rỗng; preview Unicode/NUL-separated; root sai, detached/bare bị chặn.
- Bí mật trong index/history kể cả đã xóa; literal pathspec, .gitignore symlink,
  lỗi UTF-8/quyền quét đều không tự bỏ qua.
- Timeout/mạng/quyền GitHub được mock; cancel/EOF và success actions sau push.
- Linux installer trong HOME tạm; backup, dependency failure, đường dẫn Unicode.
- Darwin installer mô phỏng trên Bash Ubuntu; clipboard pbcopy/clip/Wayland/X11 mock.
- Windows installer review cấu trúc, backup/rollback và User PATH; chưa xác minh native.

## Phạm vi môi trường chưa kiểm thử

| Nhóm | Trạng thái | Phần thiếu |
|---|---|---|
| Windows PS 5.1/7, CMD, py/python, PATH, rollback, clipboard | NOT TESTED native | Không có Windows/PowerShell |
| macOS/Bash 3.2/Zsh/Homebrew/pbcopy | NOT TESTED native | Không có macOS; mô phỏng không thay thế |
| Ubuntu 24/26, Debian, Fedora, Arch, Kali container | SKIPPED / NOT TESTED tương thích | Thiếu runtime; package/image resolution chưa kiểm tra |
| Ubuntu Server riêng / Desktop GUI | NOT TESTED | Headless unit tests không chứng nhận OS edition/GUI |
| Python 3.10–3.13 | NOT TESTED runtime | Grammar parse không chứng nhận runtime |
| GitHub thật, API/quyền/visibility/push | NOT TESTED | Không được phép ghi lên dịch vụ trong phiên |
| Review toàn diện secrets và quyền phân phối | NOT TESTED / cần duyệt | Audit mẫu không bao phủ mọi credentials; license chưa chọn |

Không cài runtime, sudo hoặc tự nâng quyền để vượt qua blocker.
Chỉ Ubuntu hiện tại đã xác minh bằng test thực thi; không công bố hỗ trợ đa nền tảng.

## Phân phối và tài liệu

- [Cài/cập nhật/gỡ](V5_INSTALL_UPDATE_UNINSTALL.md): giữ nguồn/backup, khôi phục launcher,
  tránh xóa PATH dùng chung hoặc dữ liệu dự án.
- [Bảo mật](V5_SECURITY.md): scope quét runtime/artifact, lịch sử, bảo vệ dữ liệu local.
- [Phương án license](V5_LICENSE_OPTIONS.md): nguồn chính thức MIT/Apache/GPL và
  tác động khi không có license; chỉ chuẩn bị quyết định, không áp dụng giấy phép.
- [Changelog](../CHANGELOG.md), [release notes DRAFT](V5_RELEASE_NOTES_DRAFT.md),
  [checklist](V5_RELEASE_CHECKLIST.md), [blockers](V5_RELEASE_BLOCKERS.md).

ZIP/matrix chọn chung source/test/docs/tools/installers; bỏ .git/cache/backup,
credentials theo tên, symlink và đường dẫn nguy hiểm. Audit nội dung cục bộ chặn
private-key header/GitHub token/AWS access-key-ID theo mẫu; chỉ báo path/line/rule.
Không gửi dữ liệu source/secrets ra dịch vụ kiểm tra ngoài. Có thể còn false negative;
cần review trước công khai. SHA-256/manifest không thay chữ ký xác thực tác giả.

## Bằng chứng và artifact hiện tại

Tài sản cục bộ vòng audit2 (dist bị gitignore, không upload):

- dist/git-publish-5.0.0rc1-audit2.zip — ZIP nguồn ứng viên mới.
- dist/git-publish-5.0.0rc1-audit2.zip.sha256 — checksum.
- dist/git-publish-5.0.0rc1-audit2.release-manifest.json — version, checksum, tests và gates.
- dist/verify-audit2.json — kiểm định cuối từ chính ZIP bàn giao.
- dist/pytest-v5-audit2.xml — JUnit workspace.
- dist/syntax-audit2.json — syntax/runtime discovery/source audit.
- dist/verify-audit2-pilot.json — kiểm định ZIP tạm trước chốt tài liệu.

Bản dist/git-publish-5.0.0rc1-source.zip phiên trước và checksum được giữ nguyên
(b77ba7358e8c3cbab4ca466196ceedd489e54d03ef6e44c33842b49e2978b45b).
Đó là bằng chứng cũ 42 file, không phải source mới nhất. Không ghi đè artifact cũ.

Checksum ZIP mới nằm ngoài ZIP để không tạo phụ thuộc vòng với tài liệu bên trong.
Release manifest ngoài ZIP lấy kết quả từ verifier thực tế, không tự gán native PASS.

## Lệnh tiếp tục

~~~bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python3 -B -m pytest -q -rs -p no:cacheprovider
python3 -B tools/build_snapshot.py --audit
python3 -B tools/verify_release.py dist/git-publish-5.0.0rc1-audit2.zip \
  --checksum dist/git-publish-5.0.0rc1-audit2.zip.sha256 --report dist/verify-next.json
python3 -B tools/linux_matrix.py --list
~~~

Chỉ chạy matrix --run khi runtime đã có và info đủ quyền; không tự cài runtime.
Dùng tên report/artifact mới khi kiểm định lại. LICENSE, đích GitHub, quyền ghi
dịch vụ và phê duyệt công khai vẫn thuộc chủ dự án.

## Release gates

1. P0/P1 kỹ thuật đã phát hiện: PASS, đã sửa và có regression.
2. Tests trong môi trường hiện tại: PASS; native/matrix còn NOT TESTED/SKIPPED.
3. Installer đúng nền tảng công bố: Ubuntu test PASS; không công bố nền tảng chưa thử.
4. Artifact/checksum: PASS qua verifier; xem manifest/report ngoài ZIP.
5. Tài liệu nhất quán và công khai giới hạn: PASS.
6. Secrets: PASS audit mẫu; review toàn diện NOT TESTED.
7. Danh sách nền tảng chưa thử: PASS, ghi rõ.
8. License/quyền phân phối/phê duyệt: chưa được cấp.

Do đó giữ RC. Không còn công việc kỹ thuật độc lập bắt buộc trong môi trường hiện tại
ngoài các gate cần môi trường/quyết định mới đã ghi rõ; không đánh dấu RELEASE READY.
