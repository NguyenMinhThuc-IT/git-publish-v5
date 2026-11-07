# Git Publish V5 — tiến độ

Ngày bắt đầu: 2026-11-07 (Asia/Ho_Chi_Minh).

## Quy ước

- PASS: kiểm tra đã chạy và đạt trong phạm vi ghi rõ.
- FAIL: kiểm tra đã chạy và còn lỗi.
- SKIPPED: kiểm tra bị bỏ qua có lý do.
- NOT TESTED: chưa chạy trong môi trường cần thiết.

Không commit/push dự án, không sửa origin, không cài phần mềm hệ thống.
Repository đã có thay đổi chưa commit; giữ nguyên phần việc có sẵn.
Origin hiện là repository `hi`, không phải đích phát hành Git Publish.

## Kế hoạch A–F

| Giai đoạn | Công việc | Trạng thái ban đầu |
|---|---|---|
| A | Lõi Python: remote, lỗi subprocess, Git, bảo mật, hủy | Đang thực hiện |
| B | Bộ cài Windows; test cấu trúc và runtime nếu có | NOT TESTED |
| C | Linux matrix; test offline, container khi có runtime | NOT TESTED |
| D | macOS installer, Bash/Zsh, clipboard mô phỏng | NOT TESTED |
| E | Tài liệu, đóng gói an toàn, release checklist | NOT TESTED |
| F | Regression, cú pháp, kiểm thử cuối và báo cáo | NOT TESTED |

## Baseline

- Đã đọc mã nguồn, test, tài liệu và diff hiện có.
- Lần kiểm tra trước: PASS — 54 tests trên Ubuntu, Python 3.14.4.
- Windows và macOS thực tế: NOT TESTED.
- Docker/Podman/PowerShell: chưa tìm thấy trong PATH; không tự cài đặt.
- Các test Git chỉ được dùng remote bare cục bộ trong thư mục tạm.
- Phiên bản hiện tại là 4.0.0; sẽ chuyển rõ sang 5.0.0rc1,
  cập nhật kiểm tra phiên bản tương ứng, giữ nguyên các test hành vi.

## Phát hiện cần xử lý

- Chuẩn hóa URL `ssh://git@github.com/...` chưa nhất quán.
- Lỗi mạng khi tra repository đang bị coi như repository không tồn tại.
- Quét filesystem không thấy file bí mật đã bị xóa nhưng còn trong Git.
- Cần kiểm tra subdirectory của repo cha và detached HEAD trước khi ghi.
- ZIP hiện chưa có test chống symlink ở thư mục cha/allowlist chặt.

## Nhật ký

Các kết quả từng giai đoạn sẽ được bổ sung sau khi chạy test thực tế.

### A — PASS (offline Ubuntu)

- Baseline chạy lại: 54 passed (1.30s).
- Sửa chuẩn hóa SSH, tra GitHub chỉ coi HTTP 404 là không tồn tại,
  chặn nhiều URL/push URL khác fetch, kiểm tra root/detached HEAD trước ghi.
- Quét tên đường dẫn trong index/lịch sử, kể cả file đã bị xóa; pathspec literal,
  escape ignore glob, chặn `.gitignore` symlink; kiểm tra bí mật mới sau đồng bộ.
- UTF-8 cho Git/gh; preview NUL-separated; clipboard không GUI trả False.
- Phiên bản 5.0.0rc1; cập nhật assertion phiên bản cũ có chủ đích.
- Regression bắt lỗi đổi chữ hoa/thường tên repo trong lần chạy trung gian;
  đã sửa mã để giữ nguyên tên, không bỏ test.
- Kết quả sau sửa: **92 passed (2.49s)**.
- GitHub/network thật: NOT TESTED; lỗi được mô phỏng. Push rejection và lịch sử
  được kiểm tra bằng Git thật, remote bare local trong thư mục tạm.

### B — đang thực hiện

- Không có `pwsh`/`powershell` trong PATH; Windows thực tế: NOT TESTED.
- Tiếp tục rà soát và bổ sung test offline, không cài runtime.

### B — PASS review offline; runtime NOT TESTED

- Bộ cài dùng LiteralPath, xác thực nền tảng, backup tên duy nhất,
  ghi file tạm rồi thay launcher, rollback khi lỗi và dọn file tạm.
- Bảo vệ launcher/reparse point; so sánh PATH theo từng phần tử, mở rộng biến.
- Launcher bật Python UTF-8; bỏ ExecutionPolicy Bypass, không đổi policy hệ thống.
- Thêm `-BinDir` và `-NoPathUpdate` để kiểm thử trên Windows mà không ghi User PATH.
- Có test parse PS 5.1/7 và test cài/chạy CMD/PowerShell, tự SKIPPED nếu thiếu runtime.
- Windows thực tế, Python py/python trên Windows, rollback runtime và User PATH:
  NOT TESTED trong phiên này.
- Kết quả cuối B: **93 passed, 4 skipped (2.46s)**.

### C — đang thực hiện

- Không tìm thấy Docker/Podman; container NOT TESTED, không tải image/cài runtime.
- Tiếp tục hoàn thiện runner, báo cáo và kiểm thử offline.

### C — PASS offline; container NOT TESTED

- Runner sao chép bộ test/docs/tools, mount nguồn readonly, chạy toàn bộ pytest,
  kiểm tra launcher thật không credentials, xóa DISPLAY/Wayland trong container.
- Kiểm tra quyền runtime bằng `info`, không tự nâng quyền; tiếp tục các distro
  sau lỗi; thêm JSON report, trạng thái SKIPPED khi thiếu môi trường.
- Chặn copy qua symlink thư mục cha; thêm test offline điều phối runner.
- Container 6 distro: NOT TESTED do thiếu Docker/Podman.
- Kết quả cuối C: **99 passed, 4 skipped (2.47s)**.

### D — đang thực hiện

- macOS thật và Bash 3.2 của Apple: NOT TESTED trên máy Ubuntu.
- Sẽ kiểm tra installer trong fixture Darwin mô phỏng và clipboard bằng mock.

### D — PASS mô phỏng/offline; macOS NOT TESTED

- Installer Linux/macOS chạy bằng Bash trên Ubuntu với uname Darwin giả lập;
  kiểm tra đường dẫn Unicode/dấu cách, truyền đối số và exit code thật.
- Launcher ghim Python đã kiểm tra, bật UTF-8; chặn đích là thư mục,
  giữ launcher cũ nếu kiểm tra dependency hoặc backup thất bại.
- Unit tests pbcopy/clip/Wayland/X11, timeout/fallback và headless;
  không truy cập clipboard thật. Console ASCII không làm CLI crash.
- Zsh, Bash 3.2/macOS thật: NOT TESTED; test Zsh tự SKIPPED nếu thiếu.
- Kết quả cuối D: **113 passed, 5 skipped (2.84s)**.

### E — đang thực hiện

- Hoàn thiện tài liệu V5, checklist và allowlist đóng gói; không tự chọn license.

### E — PASS kiểm thử đóng gói/tài liệu

- README, hướng dẫn, troubleshooting, bảng tương thích và release checklist V5.
- ZIP chỉ lấy source/test/docs/installers/tools theo allowlist, bỏ symlink kể cả
  thư mục cha, credentials theo tên, .git/cache/backup; không ghi ngoài workspace mặc định.
- Manifest từng file, SHA-256 ZIP, CRC/verify không extract, không overwrite artifact.
- Kết quả cuối E trước kiểm tra F: **134 passed, 5 skipped (2.53s)**.
- Giới hạn: không chứng nhận mọi bí mật nhúng trong source; LICENSE trống.

### F — đang thực hiện

- Rà soát lần cuối, bổ sung kiểm tra docs/edge cases; sau đó chạy toàn bộ test,
  syntax Python/Bash và kiểm tra ZIP nguồn được giải nén trong thư mục tạm.

### F — PASS trong môi trường hiện có

- Rà soát cuối phát hiện Git probe cần phân biệt bare repo; đã chặn trước ghi,
  thêm regression xác minh bare repo tạm giữ nguyên từng file.
- Pytest workspace: **146 passed, 5 skipped (3.41s)**, 151 collected.
- Pytest từ ZIP giải nén tạm: **146 passed, 5 skipped (3.40s)**.
- Python: 30 file compile/parse; grammar 3.10 PASS, runtime 3.10–3.13 NOT TESTED.
- Bash syntax hai installer: PASS. PowerShell/Zsh: SKIPPED do thiếu runtime.
- ZIP thử: 42 file nguồn + manifest, CRC/hash/roundtrip PASS.
- Giữ nguyên toàn bộ metadata .git theo hash; không commit/push/sửa origin.
- Bằng chứng máy đọc trong dist/: JUnit, syntax-check, packaging-check,
  linux-matrix-status; báo cáo chi tiết: V5_FINAL_REPORT.md.

## Trạng thái bàn giao

| Giai đoạn | Kết quả trong phiên | Phần chưa xác minh |
|---|---|---|
| A | PASS offline/Git local | GitHub và mạng thật NOT TESTED |
| B | PASS review/test cấu trúc | Windows/PS/CMD runtime NOT TESTED |
| C | PASS runner offline | Sáu container SKIPPED; native distro NOT TESTED |
| D | PASS mô phỏng/Bash Ubuntu | macOS/Bash 3.2/Zsh native NOT TESTED |
| E | PASS docs/packaging tests | LICENSE và review bí mật nội dung trước phát hành |
| F | PASS 146 tests; 5 SKIPPED | Không chứng nhận tương thích toàn nền tảng |

Mã nguồn 5.0.0rc1 đã sẵn sàng để tiếp tục QA trên môi trường còn thiếu.
Chưa phê duyệt phát hành công khai. Không tự giải quyết giấy phép hoặc đổi đích Git.

## Tiếp tục Autonomous Release Engineering — 2026-11-07

Đã đọc chỉ dẫn đính kèm, kiểm chứng lại báo cáo và phát hiện file
V5_RELEASE_BLOCKERS.md chưa tồn tại; đã tạo với phân loại P0/P1/P2 và gate.

### Phase 1–2: audit và ổn định lõi

- Baseline thực tế trước sửa: **146 passed, 5 skipped (3.24s)**.
- Regression trước sửa chứng minh 8 failures: fast-forward ghi đè ignored file,
  matrix copy credentials.py và 6 tình huống thư mục/dotfile xác thực không được phát hiện.
- SEC-01: merge fast-forward thêm --no-overwrite-ignore; giữ nguyên HEAD và file local
  khi remote có đường dẫn trùng. Test remote đổi sau prepare cũng xác nhận push bị reject.
- SEC-02: matrix dùng chung allowlist ZIP, bỏ code copy trùng lặp.
- SEC-03: bảo vệ .aws/.ssh/.gnupg và .netrc/.npmrc/.pypirc bằng tên/đường dẫn;
  không đọc nội dung thư mục xác thực thật.
- Kết quả sau sửa: **155 passed, 5 skipped (3.88s)**.
- Thêm audit nội dung mẫu credentials biết trước cho ZIP/matrix; chỉ xuất path/line/rule,
  không xuất giá trị khớp. Regression dữ liệu tổng hợp, không dùng secrets thật.

### Phase 3–6: đang tiếp tục

- Runtime Docker/Podman/PowerShell/Zsh vẫn không có; không cài lại hoặc giả định đã PASS.
- Bổ sung phần còn thiếu: cập nhật/gỡ cài, bảo mật, changelog, release notes draft,
  lựa chọn license có nguồn chính thức, manifest/checksum và kiểm định artifact mới.
- Giữ nguyên ZIP phiên trước làm bằng chứng cũ; artifact mới sẽ dùng tên khác.

### Phase 3–6: PASS phần thực hiện được

- Runtime vẫn thiếu: PowerShell/Zsh/Docker/Podman và Python 3.10–3.13. Native
  Windows/macOS/Server/GUI và GitHub thật tiếp tục NOT TESTED; không cài phần mềm.
- Content audit: **159 passed, 5 skipped (3.88s)**; verifier ban đầu:
  **166 passed, 5 skipped (3.69s)**.
- Thêm gate fail khi thiếu JUnit, timeout, checksum sai, missing manifest hoặc
  suite toàn SKIPPED; không coi exit code 0 là đủ bằng chứng.
- Bộ test hiện tại: **170 passed, 5 skipped (3.76s)**, 175 collected, không FAIL.
- ZIP pilot qua verifier thật: **170 passed, 5 skipped** từ nguồn giải nén cô lập.
- Python compile/parse: **32 file PASS**; Bash syntax hai installer PASS.
- Audit nguồn: **50 file PASS với mẫu credentials biết trước**, không xuất giá trị.
- Đã bổ sung cài/cập nhật/gỡ, bảo mật, license options có nguồn chính thức,
  CHANGELOG, release notes draft, blockers và checklist. LICENSE vẫn trống.

### Phase 7: bàn giao RC, chưa duyệt công khai

- P0/P1 kỹ thuật chưa xử lý đã biết: 0. SEC-01/02/03 và DIST-01/QA-01 đã FIXED/PASS.
- Chín gate trong V5_RELEASE_BLOCKERS.md còn cần môi trường, review hoặc chủ dự án.
- Version giữ **5.0.0rc1**; không tạo tag, commit/push, đổi origin hoặc chọn license.
- Artifact audit2 dùng tên mới; manifest/checksum/report trong dist; bản cũ giữ nguyên.
- Xem V5_FINAL_REPORT.md để biết kết quả hiện tại; số liệu A–F bên trên là lịch sử.
