# Git Publish V5.0.1

**Git Publish — Publish your projects to GitHub easily.**

CLI Python giúp chuẩn bị và đưa dự án lên GitHub qua Git và GitHub CLI,
có bộ cài cho Windows, Linux và macOS.

**V5.0.1 bổ sung Windows Auto Installer:** chạy `setup.cmd` để tự nhận diện
Python tương thích, kiểm tra Git/GitHub CLI và đề xuất cài dependency sau khi bạn xác nhận.

## Download

### [⬇ Download Git Publish V5.0.1 ZIP — Development Build](https://github.com/NguyenMinhThuc-IT/git-publish-v5/archive/refs/heads/feature/v5.0.1-auto-installer.zip)

**Trạng thái: Development Build.** Tại thời điểm xác minh ngày 10/11/2026,
chưa có tag hoặc GitHub Release chính thức `v5.0.1`. ZIP trên lấy mã nguồn từ nhánh
`feature/v5.0.1-auto-installer` và có thể thay đổi khi nhánh được cập nhật.

Windows: **tải ZIP → giải nén → chạy `setup.cmd`**.
Tên ZIP GitHub cung cấp: `git-publish-v5-feature-v5.0.1-auto-installer.zip`.

Xem [cài đặt, cập nhật và gỡ](docs/V5_INSTALL_UPDATE_UNINSTALL.md),
[xử lý lỗi winget](#troubleshooting) hoặc [bản V5.0.0 trước đó](#previous-releases).

## Quick Start

1. Tải ZIP ở trên và giải nén vào thư mục mới.
2. Mở thư mục gốc đã giải nén, nơi có `setup.cmd`; nhấp đúp file này,
   hoặc chạy trong PowerShell (thay đường dẫn ví dụ bằng thư mục của bạn):

   ```powershell
   cd "C:\duong dan\git-publish-v5-feature-v5.0.1-auto-installer"
   .\setup.cmd
   ```

3. Xem kết quả kiểm tra Python, Git, GitHub CLI và `winget`.
   Nếu cần cài/cập nhật dependency, đọc đề xuất rồi nhập `y` để đồng ý từng thay đổi.
   Từ chối hoặc không có dữ liệu nhập sẽ dừng trước khi cài gói nào.
4. Khi setup hoàn tất, mở **PowerShell mới** và kiểm tra launcher:

   ```powershell
   Get-Command publish
   where.exe publish
   ```

   Mặc định lệnh trỏ tới `publish.cmd` trong `$HOME\.local\bin`.
   Hai lệnh trên chỉ kiểm tra đường dẫn; để sử dụng, xem [Usage](#usage).

Chi tiết về nơi cài ứng dụng, Python được chọn và tùy chọn nâng cao ở [Installation](#installation).

## Features

- **Windows Auto Installer:** một điểm vào `setup.cmd`, kiểm tra dependency trước khi cài ứng dụng.
- **Tự nhận diện Python tương thích:** dò nhiều interpreter, chạy thử và ghim đường dẫn
  Python đã chọn cho launcher; không đổi Python mặc định của máy.
- **Kiểm tra Git và GitHub CLI:** kiểm tra phiên bản lẫn tính năng bằng probe offline,
  không chặn phiên bản mới hơn nếu đáp ứng yêu cầu.
- **Cài dependency có xác nhận:** đề xuất cài thành phần thiếu hoặc nâng Git/gh không
  tương thích qua `winget`; không nâng công cụ đang tương thích, không ép gỡ hay hạ cấp phần mềm.
- **Hỗ trợ đường dẫn Unicode và khoảng trắng**, sao lưu launcher khi cài lại và giữ các bản ứng dụng cũ.
- **Publish tương tác:** chọn file bảo vệ, xem danh sách staging, xác nhận commit/push;
  mặc định repository mới là Private, giữ visibility của repository đã tồn tại.

## Requirements & Compatibility

| Thành phần | Yêu cầu |
| --- | --- |
| Windows setup | Windows PowerShell 5.1+; Python bản ổn định 3.11–3.15 trong phạm vi dò của setup |
| Linux/macOS | Python 3.10 trở lên; Bash để chạy installer |
| Git | Windows setup yêu cầu Git ≥2.23 và các probe tính năng đạt |
| GitHub CLI (`gh`) | Có các tính năng `api --jq`, `repo create --private/--public`, `repo view --json`, `auth status` |
| `winget` | Cần hoạt động khi Windows setup phải cài/cập nhật dependency; không bắt buộc nếu đã đủ dependency |
| GitHub | Đăng nhập bằng `gh auth login` trước khi publish thật; bộ cài không tự đăng nhập |

Runtime Python chỉ dùng thư viện chuẩn; `requirements.txt` không có dependency.
Chạy bộ test cần cài `pytest` riêng. Linux/macOS installer yêu cầu Python, Git và gh có sẵn.

**Python trên Windows:** setup ưu tiên 3.14, sau đó chọn phiên bản ổn định mới nhất
trong phạm vi 3.11–3.15; loại interpreter lỗi, prerelease và phiên bản ngoài phạm vi.
CI V5.0.1 đã PASS với Windows 3.11–3.15 (xem [Testing](#testing)), nhưng workflow
vẫn đánh dấu lane 3.15 là thử nghiệm (`continue-on-error`). Setup hiện chỉ đánh dấu
3.14 là đã kiểm thử nên vẫn có thể cảnh báo với các bản khác; PASS của lane 3.15
không đồng nghĩa công bố hỗ trợ chính thức phiên bản này.

Ubuntu, Windows và macOS đã có CI. macOS chưa được xác minh trên máy Mac cá nhân;
Debian, Fedora, Arch và Kali chưa được kiểm thử riêng.

## Installation

### Windows

Dùng các bước [Quick Start](#quick-start). `setup.cmd` gọi
`installers/setup-windows.ps1`; quá trình cài thực hiện như sau:

1. Dò Python qua `py -0p`, registry PEP 514, PATH và các thư mục cài phổ biến;
   chạy thử interpreter theo quy tắc ở [Requirements & Compatibility](#requirements--compatibility).
2. Kiểm tra Git/gh và hiển thị dependency đã phát hiện. Probe Git dùng repository tạm
   để kiểm tra branch, staging, pathspec; probe gh dùng help, không kết nối GitHub.
3. Nếu cần thay đổi, xin xác nhận riêng từng gói và thu đủ xác nhận **trước lần cài đầu tiên**.
   Dùng source `winget` và ID chính xác `Python.Python.3.14`, `Git.Git`, `GitHub.cli`.
   Python được cài thêm phạm vi user với `--no-upgrade`; chỉ nâng Git/gh khi probe không đạt.
   Đề xuất nêu việc chấp nhận điều khoản gói/nguồn; một số gói có thể yêu cầu UAC.
4. Xác minh lại dependency, rồi sao chép ứng dụng vào
   `%LOCALAPPDATA%\GitPublish\releases\5.0.1-<id>`. Mỗi lần cài tạo thư mục riêng,
   giữ các bản cũ/cấu hình; không sao chép `.git`, credentials hay cache từ nguồn.
5. Tạo `publish.cmd` và `publish-runner.ps1` trong `$HOME\.local\bin`, sao lưu launcher cũ,
   cập nhật User PATH. `install-state.json` trong thư mục ứng dụng lưu Python tuyệt đối
   đã xác minh; launcher ghim Python này và thêm thư mục Git/gh đã chọn vào PATH của tiến trình.

Có thể xóa thư mục ZIP đã giải nén sau khi setup thành công. Nếu Python đã chọn bị
di chuyển/gỡ, chạy lại `setup.cmd` từ bản nguồn để chọn lại. Các bản ứng dụng cũ không tự bị xóa.

Setup PowerShell nhận `-InstallRoot`, `-BinDir` và `-NoPathUpdate`. Ví dụ cài launcher
vào thư mục riêng và bỏ qua cập nhật PATH:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\installers\setup-windows.ps1 -BinDir "C:\Users\ten\Tools\GitPublish" -NoPathUpdate
```

Bộ cài trực tiếp dành cho máy đã đủ dependency:

```powershell
.\installers\install.ps1 -PythonPath "C:\Python314\python.exe"
```

Installer trực tiếp cũng nhận `-BinDir`, `-NoPathUpdate` và **tham chiếu thư mục nguồn
hiện tại**, nên cần giữ thư mục đó. Launcher `publish.ps1` cũ được sao lưu và thay
bằng script nội bộ `publish-runner.ps1`, để PowerShell tìm thấy `publish.cmd` khi gọi `publish`.

Setup và launcher dùng `-ExecutionPolicy Bypass` chỉ cho tiến trình PowerShell con;
không sửa execution policy User/Machine. Group Policy của tổ chức vẫn có hiệu lực.

### Linux

```bash
cd "/duong dan/git-publish"
bash installers/install.sh
export PATH="$HOME/.local/bin:$PATH"
```

### macOS

```bash
cd "/duong dan/git-publish"
bash installers/install-macos.sh
export PATH="$HOME/.local/bin:$PATH"
```

Linux/macOS: giữ thư mục nguồn sau cài vì launcher tham chiếu trực tiếp `publish.py`.
Để lưu PATH, thêm dòng `export` trên vào `~/.bashrc` với Bash tương tác hoặc `~/.zshrc`
với Zsh. Installer chỉ hướng dẫn, không sửa profile.

### Cập nhật, khôi phục và tài liệu

Giải nén bản mới vào thư mục khác, chạy installer rồi kiểm tra launcher trong terminal mới.
Giữ nguồn/backup cũ cho đến khi xác minh; không chạy đồng thời hai installer.
Xem [hướng dẫn cập nhật, khôi phục và gỡ mà giữ dữ liệu](docs/V5_INSTALL_UPDATE_UNINSTALL.md).

- [Hướng dẫn sử dụng](docs/HUONG_DAN_SU_DUNG.md)
- [Báo cáo tương thích](docs/HO_TRO_HE_DIEU_HANH.md)
- [Bảo mật](docs/V5_SECURITY.md)
- [Changelog](CHANGELOG.md)

Một số báo cáo ghi lại các đợt kiểm định trước; kết quả CI V5.0.1 được nêu tại [Testing](#testing).

## Usage

Đăng nhập GitHub thủ công khi cần dùng thật, sau đó vào **thư mục gốc của dự án cần publish**:

```powershell
gh auth login
cd "C:\duong dan\du an cua ban"
publish
```

Trên Linux/macOS cũng dùng `gh auth login`, vào thư mục dự án rồi chạy `publish`.
Windows có thể gọi rõ `publish.cmd` từ CMD hoặc PowerShell.
Header ứng dụng hiển thị `Git Publish v5.0.1` để kiểm tra phiên bản đang chạy.
Lệnh `publish` mở luồng tương tác, có thể tạo repository GitHub, commit và push sau xác nhận.

Ứng dụng kiểm tra dependency/đăng nhập, xác định repository, cho chọn file bảo vệ,
stage và preview, hỏi xác nhận commit hoặc push commit hiện có.
Origin khác đích, nhiều URL hoặc URL push khác fetch sẽ bị chặn.
Không tự đổi origin, merge lịch sử phân nhánh hoặc force push.

### Bảo mật và giới hạn

- Quét tên/đuôi/đường dẫn filesystem, index và lịch sử Git reachable; không đọc nội dung file bí mật.
- Enter ở bước bảo vệ chọn tất cả. Bỏ bảo vệ cần xác nhận riêng.
- `.gitignore` không xóa dữ liệu đã commit. Đường dẫn được bảo vệ còn trong lịch sử sẽ chặn publish.
- Preview chỉ hiển thị tên/trạng thái file, không phải toàn bộ diff nội dung.
- Bộ quét không đảm bảo phát hiện mọi bí mật, đặc biệt bí mật nhúng trong mã nguồn
  hoặc lịch sử chưa có ở local. Luôn tự kiểm tra trước khi công khai.
- Hủy sau stage giữ nguyên staging area; không tự rollback commit đã tạo.
- URL luôn được in ra terminal; clipboard/trình duyệt là tùy chọn.

## Testing

**V5.0.1: 14/14 jobs PASS** tại
[GitHub Actions run 42482328578](https://github.com/NguyenMinhThuc-IT/git-publish-v5/actions/runs/42482328578),
nhánh `feature/v5.0.1-auto-installer`, commit `8cf2e3e2973be0322b38c33cba578389bff6a22b`.

| Nhóm CI | Cấu hình | Số jobs | Kết quả |
| --- | --- | --- | --- |
| Ubuntu | Python 3.10, 3.11, 3.12, 3.13, 3.14 | 5 | PASS |
| Windows | Python 3.11, 3.12, 3.13, 3.14, 3.15 (thử nghiệm) | 5 | PASS |
| macOS | Python 3.14 | 1 | PASS |
| Installer smoke | Ubuntu, Windows, macOS | 3 | PASS |
| **Tổng** | | **14** | **PASS** |

Test điều phối dependency Windows dùng mock cho thao tác package manager.
Installer smoke chạy launcher thật với entry point mẫu trong thư mục tạm,
không publish dự án thật. **Kết quả này không xác nhận việc cài dependency thật
bằng `winget` thành công trên mọi máy Windows**, đặc biệt máy mới chưa có dependency.

### Lệnh kiểm thử và đóng gói dành cho người phát triển

Các lệnh sau cần môi trường đã có `pytest`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q -p no:cacheprovider
bash -n installers/install.sh installers/install-macos.sh
python3 -B tools/linux_matrix.py --list
python3 -B tools/build_snapshot.py
```

ZIP do `tools/build_snapshot.py` tạo trong `dist/` loại `.git`, credentials theo tên,
symlink, backup và cache; không ghi đè ZIP cũ. Manifest SHA-256 kiểm tra tính toàn vẹn,
không thay thế rà soát bí mật nhúng trong source. ZIP nhánh GitHub ở phần Download
không phải artifact do công cụ này đóng gói và không đi kèm sidecar SHA-256 của công cụ.

Khi có Docker/Podman và quyền chạy, lệnh sau tải image và cài dependency
**bên trong container**, cần mạng:

```bash
python3 -B tools/linux_matrix.py --run all --report dist/linux-matrix.json
```

Runner chạy pytest và installer, không xác minh clipboard GUI hoặc GitHub thật.
Exit code: 0 = tất cả PASS, 1 = có FAIL, 2 = SKIPPED do thiếu môi trường.

### Kiểm định ứng viên trước phân phối

```bash
python3 -B tools/build_snapshot.py --audit
python3 -B tools/verify_release.py dist/candidate.zip \
  --checksum dist/candidate.zip.sha256 --report dist/verify-new.json
```

Thay tên `candidate.zip` và sidecar bằng artifact đã tạo. Verifier chỉ dành cho
source ZIP tin cậy, chạy pytest từ thư mục giải nén tạm. Audit mẫu credentials
không thay thế review nội dung toàn diện. Trạng thái gồm PASS/FAIL/SKIPPED/NOT TESTED;
thiếu runtime không được coi là PASS.

Tài liệu kiểm định: [tiến độ A–F](docs/V5_PROGRESS.md),
[release checklist](docs/V5_RELEASE_CHECKLIST.md), [báo cáo cuối](docs/V5_FINAL_REPORT.md),
[release notes nháp](docs/V5_RELEASE_NOTES_DRAFT.md) và [release blockers](docs/V5_RELEASE_BLOCKERS.md).
Các ghi chú lịch sử cần được đọc cùng kết quả CI nêu trên.

## Troubleshooting

### Windows không có winget hoặc App Installer đã có nhưng winget chưa hoạt động

Kiểm tra trong PowerShell:

```powershell
Get-Command winget -ErrorAction SilentlyContinue
winget --version
```

Nếu chưa có `winget`, cài/cập nhật **App Installer** từ
[Microsoft Store](https://apps.microsoft.com/detail/9nblggh4nns1), rồi mở terminal mới và kiểm tra lại.
Theo [hướng dẫn Microsoft về WinGet](https://learn.microsoft.com/windows/package-manager/winget/),
WinGet đi kèm App Installer và cần Windows 10 1809 (build 17763) trở lên.
App Installer đã hiện trong máy không đảm bảo lệnh `winget` đã được đăng ký và hoạt động.

Nếu vừa đăng nhập Windows lần đầu, quá trình đăng ký có thể chưa hoàn tất.
Làm theo phần **Install WinGet** trong tài liệu Microsoft ở trên để yêu cầu đăng ký;
nếu lệnh vẫn lỗi, xem [các vấn đề thường gặp của Microsoft](https://github.com/microsoft/winget-cli/tree/master/doc/troubleshooting#common-issues)
về phiên bản App Installer và PATH. Chỉ dùng nguồn chính thức của Microsoft.

Cách khác: cài dependency thủ công từ [Python](https://www.python.org/downloads/windows/),
[Git for Windows](https://git-scm.com/downloads/win) và [GitHub CLI](https://cli.github.com/),
rồi chạy lại `setup.cmd`. Nếu Python, Git và gh đã tương thích, setup không cần `winget`.
Lỗi mạng/winget hoặc xác minh dependency không đạt sẽ dừng; kiểm tra thông báo trước khi thử lại.
Setup không tự gỡ hoặc hạ cấp dependency để xử lý lỗi.

### Không tìm thấy publish hoặc đang chạy bản cũ

Mở terminal mới, kiểm tra `Get-Command publish -All` và `where.exe publish` trên Windows
hoặc `command -v publish` trên Linux/macOS. Với Windows, xác minh `$HOME\.local\bin`
có trong User PATH (hoặc thư mục `-BinDir` bạn đã chọn). Nếu dùng `-NoPathUpdate`,
tự thêm thư mục launcher vào PATH hoặc gọi `publish.cmd` bằng đường dẫn đầy đủ.
Chạy lại setup nếu Python đã ghim bị di chuyển/gỡ.

Nếu script bị Group Policy của tổ chức chặn, liên hệ quản trị viên.
Với lỗi đăng nhập, kiểm tra `gh auth status`; xem thêm
[hướng dẫn và troubleshooting](docs/HUONG_DAN_SU_DUNG.md).

## Previous Releases

[**Git Publish V5.0.0 — bản phát hành chính thức trước đó**](https://github.com/NguyenMinhThuc-IT/git-publish-v5/releases/tag/v5.0.0).
Trang Release có mục **Source code (zip)** để tải đúng mã nguồn V5.0.0.

V5.0.0 có [10/10 jobs CI PASS tại run 42355854261](https://github.com/NguyenMinhThuc-IT/git-publish-v5/actions/runs/42355854261)
và đã kiểm thử publish thực tế trên Windows. Đây là kết quả của V5.0.0;
trạng thái CI V5.0.1 được ghi riêng ở [Testing](#testing).

## License

File [LICENSE](LICENSE) hiện trống; repository chưa nêu giấy phép sử dụng cụ thể.
Chủ dự án cần quyết định giấy phép trước khi phát hành V5.0.1.
Xem [các phương án giấy phép](docs/V5_LICENSE_OPTIONS.md).
