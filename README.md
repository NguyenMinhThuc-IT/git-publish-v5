# Git Publish V5 — 5.0.1

CLI Python giúp chuẩn bị và đưa dự án lên GitHub qua Git và GitHub CLI.

V5.0.1 bổ sung Windows one-click setup và lựa chọn Python động.
V5.0.0 đã phát hành; V5.0.1 cần kiểm thử CI mới trước khi phát hành.
Xem [báo cáo cuối](docs/V5_FINAL_REPORT.md) và [hỗ trợ hệ điều hành](docs/HO_TRO_HE_DIEU_HANH.md).

## Trạng thái kiểm thử Git Publish V5.0.0

Git Publish V5.0.0 đã vượt qua **10/10 job GitHub Actions**.

| Nền tảng                  | Kết quả |
| ------------------------- | ------- |
| Ubuntu — Python 3.10–3.14 | PASS    |
| Windows — Python 3.14     | PASS    |
| macOS — Python 3.14       | PASS    |
| Installer Ubuntu          | PASS    |
| Installer Windows         | PASS    |
| Installer macOS           | PASS    |

**Ghi chú:**

- Windows đã được kiểm thử publish thực tế.
- macOS đã được kiểm thử trên GitHub Actions nhưng chưa xác minh trên máy Mac cá nhân.
- Debian, Fedora, Arch và Kali chưa được kiểm thử riêng.

[Xem kết quả CI](https://github.com/NguyenMinhThuc-IT/git-publish-v5/actions/runs/42355854261).

## Yêu cầu

- Linux/macOS: Python 3.10 trở lên. Windows setup: Python ổn định 3.11–3.15.
- Git và GitHub CLI (gh); kiểm tra phiên bản và tính năng, không đặt giới hạn tối đa.
- Khi sử dụng GitHub thật: đăng nhập trước bằng gh auth login.
- Runtime Python chỉ dùng thư viện chuẩn; requirements.txt không có dependency.
- Chạy test cần pytest đã cài. Windows setup chỉ cài/cập nhật dependency sau khi đồng ý.
- Linux/macOS installer yêu cầu dependency có sẵn. Không bộ cài nào tự đăng nhập GitHub.

## Cài đặt

Giải nén ZIP nguồn hoặc dùng bản nguồn đã được kiểm tra. Trên Linux/macOS, giữ
nguyên thư mục nguồn sau khi cài: launcher tham chiếu trực tiếp tới publish.py.

Linux:

~~~bash
cd "/duong/dan/git-publish"
bash installers/install.sh
export PATH="$HOME/.local/bin:$PATH"
~~~

macOS (đã kiểm thử trên GitHub Actions, chưa xác minh trên máy Mac cá nhân):

~~~bash
cd "/duong/dan/git-publish"
bash installers/install-macos.sh
export PATH="$HOME/.local/bin:$PATH"
~~~

Để lưu PATH, thêm dòng export trên vào cấu hình shell:
~/.bashrc với Bash tương tác hoặc ~/.zshrc với Zsh.
Installer chỉ hướng dẫn, không sửa profile.

Windows — giải nén ZIP và nhấp đúp **setup.cmd** tại thư mục gốc:

~~~powershell
cd "C:\duong dan\git-publish"
.\setup.cmd
~~~

Cần Windows PowerShell 5.1+ (có sẵn trên Windows 10/11). Setup sẽ:

1. Dò Python qua launcher `py -0p`, registry PEP 514, PATH và các thư mục cài phổ biến;
   chạy thử từng interpreter, loại bản lỗi, prerelease và bản ngoài mục tiêu 3.11–3.15.
2. Ưu tiên Python 3.14 đã có bằng chứng CI Windows của V5.0.0, sau đó chọn bản ổn định
   mới nhất trong mục tiêu. 3.11–3.13 và 3.15 được cảnh báo chưa kiểm thử Windows
   cho bản mới; **3.15 là thử nghiệm, chưa công bố hỗ trợ** cho tới khi CI đầy đủ PASS.
   Không sửa Python mặc định, không gỡ/hạ cấp phiên bản của dự án khác.
3. Hiển thị Python, Git, gh và winget. Git cần >=2.23 và các probe branch/staging/pathspec;
   gh cần các tính năng api --jq, repo create/view --json, auth status.
   Phiên bản mới hơn không bị chặn nếu các probe đạt. Probe không kết nối GitHub.
4. Nếu thiếu hoặc không tương thích, xin phép riêng từng thay đổi trước khi cài gói nào.
   Dùng winget source `winget`, ID chính xác `Python.Python.3.14`, `Git.Git`, `GitHub.cli`.
   Python được cài thêm phạm vi user với `--no-upgrade`; chỉ nâng Git/gh khi probe không đạt.
   Gói có thể yêu cầu UAC/điều khoản nguồn. Từ chối/EOF sẽ dừng an toàn.
5. Xác minh lại dependency, sao chép ứng dụng vào `%LOCALAPPDATA%\GitPublish\releases\5.0.1-<id>`
   rồi gọi installer Windows hiện có. Mỗi lần cài giữ lại mã nguồn cũ và cấu hình;
   không sao chép `.git`, credentials hay cache từ ZIP/thư mục nguồn.
6. Tạo `publish.cmd` và `publish-runner.ps1` trong `$HOME\.local\bin`, backup launcher cũ,
   cập nhật User PATH. `install-state.json` trong thư mục ứng dụng lưu đường dẫn Python
   tuyệt đối đã xác minh; launcher ghim chính đường dẫn đó và thư mục Git/gh đã chọn.

Mở terminal mới rồi chạy `publish` trong dự án. Có thể xóa thư mục ZIP đã giải nén sau
khi setup hoàn tất. Không tự chạy `gh auth login`; đăng nhập thủ công khi cần dùng thật.
Cài lại bằng `setup.cmd` để chọn lại Python nếu interpreter đã bị di chuyển/gỡ.
Các bản ứng dụng cũ được giữ lại; không tự xóa để tránh mất dữ liệu tùy chỉnh.

Thiếu winget: cài/cập nhật **App Installer** từ [Microsoft Store](https://aka.ms/getwinget)
hoặc theo [hướng dẫn Microsoft](https://learn.microsoft.com/windows/package-manager/winget/).
Không tải bộ cài từ nguồn ngẫu nhiên. Có thể cài thủ công từ
[Python](https://www.python.org/downloads/windows/), [Git](https://git-scm.com/downloads/win),
[GitHub CLI](https://cli.github.com/) rồi chạy lại setup. Lỗi mạng/winget hoặc xác minh
không đạt sẽ dừng; kiểm tra lỗi rồi chạy lại, không tự gỡ/hạ cấp dependency.

Setup và launcher dùng `-ExecutionPolicy Bypass` chỉ cho tiến trình PowerShell con;
không sửa execution policy User/Machine. Chính sách Group Policy của tổ chức vẫn có
hiệu lực; nếu bị chặn, liên hệ quản trị viên. Bộ cài trực tiếp dành cho máy đã đủ dependency:

~~~powershell
.\installers\install.ps1 -PythonPath "C:\Python314\python.exe"
~~~

Bộ cài trực tiếp tham chiếu thư mục nguồn hiện tại. Có thể dùng `-BinDir` và
`-NoPathUpdate`. Setup PowerShell cũng nhận hai tùy chọn này và `-InstallRoot`.
Launcher `publish.ps1` cũ được backup và thay bằng tên nội bộ `publish-runner.ps1`
để lệnh `publish` trong PowerShell gọi được `publish.cmd`.
V5.0.1 cần xác minh Windows CI và máy Windows thật; kết quả 10/10 ở trên thuộc V5.0.0.

## Sử dụng

Vào **thư mục gốc** của dự án cần publish, chạy:

~~~text
publish
~~~

Trên Windows có thể dùng rõ publish.cmd từ CMD hoặc PowerShell.
Ứng dụng kiểm tra dependency/đăng nhập, xác định repository, cho chọn file bảo vệ,
stage và preview, hỏi xác nhận commit hoặc push commit hiện có.
Private là mặc định; repo đã tồn tại giữ nguyên visibility.

Origin khác đích, nhiều URL hoặc URL push khác fetch sẽ bị chặn.
Không tự đổi origin, merge lịch sử phân nhánh hoặc force push.
Chạy publish thực tế có thể tạo repo GitHub, commit và push sau các bước tương tác.
Smoke test CI dùng thư mục tạm và entry point mẫu, không publish dự án thật.

## Bảo mật và giới hạn

- Quét tên/đuôi/đường dẫn filesystem, index và lịch sử Git reachable; không đọc nội dung file bí mật.
- Enter ở bước bảo vệ chọn tất cả. Bỏ bảo vệ cần xác nhận riêng.
- .gitignore không xóa dữ liệu đã commit. Đường dẫn được bảo vệ còn trong lịch sử sẽ chặn publish.
- Preview chỉ hiển thị tên/trạng thái file, không phải toàn bộ diff nội dung.
- Bộ quét không đảm bảo phát hiện mọi bí mật, đặc biệt bí mật nhúng trong mã nguồn
  hoặc lịch sử chưa có ở local. Luôn tự kiểm tra trước khi công khai.
- Hủy sau stage giữ nguyên staging area; không tự rollback commit đã tạo.
- URL luôn được in ra terminal; clipboard/trình duyệt là tùy chọn.

## Kiểm thử và đóng gói

~~~bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest -q -p no:cacheprovider
bash -n installers/install.sh installers/install-macos.sh
python3 -B tools/linux_matrix.py --list
python3 -B tools/build_snapshot.py
~~~

ZIP được tạo mới trong dist/, loại .git, credentials theo tên, symlink,
backup và cache. Manifest SHA-256 kiểm tra tính toàn vẹn; không thay thế rà soát
bí mật nhúng trong source. Không ghi đè ZIP cũ.

Chỉ khi Docker/Podman có sẵn và có quyền, runner mới có thể chạy container.
Lệnh sau tải image và cài dependency **bên trong container**, cần mạng:

~~~bash
python3 -B tools/linux_matrix.py --run all --report dist/linux-matrix.json
~~~

Runner chạy pytest và installer; không xác minh clipboard GUI hoặc GitHub thật.
Exit code: 0 = tất cả PASS, 1 = có FAIL, 2 = SKIPPED do thiếu môi trường.

## Tài liệu

- [Hướng dẫn và troubleshooting](docs/HUONG_DAN_SU_DUNG.md)
- [Báo cáo tương thích](docs/HO_TRO_HE_DIEU_HANH.md)
- [Tiến độ A–F](docs/V5_PROGRESS.md)
- [Release checklist](docs/V5_RELEASE_CHECKLIST.md)
- [Báo cáo cuối](docs/V5_FINAL_REPORT.md)
- [Cài đặt, cập nhật và gỡ](docs/V5_INSTALL_UPDATE_UNINSTALL.md)
- [Bảo mật](docs/V5_SECURITY.md)
- [Changelog](CHANGELOG.md)
- [Release notes nháp](docs/V5_RELEASE_NOTES_DRAFT.md)
- [Release blockers](docs/V5_RELEASE_BLOCKERS.md)
- [Phương án giấy phép để chủ dự án quyết định](docs/V5_LICENSE_OPTIONS.md)

## Kiểm định ứng viên trước phân phối

~~~bash
python3 -B tools/build_snapshot.py --audit
python3 -B tools/verify_release.py dist/candidate.zip \
  --checksum dist/candidate.zip.sha256 --report dist/verify-new.json
~~~

Verifier chỉ dành cho source ZIP tin cậy, chạy pytest từ thư mục giải nén tạm.
Audit mẫu credentials không thay thế review nội dung toàn diện. Kiểm tra được
ghi theo PASS/FAIL/SKIPPED/NOT TESTED; thiếu runtime không được coi là PASS.

LICENSE hiện trống. Chủ dự án cần quyết định giấy phép trước phát hành.
Không tạo tag/Release V5.0.1 trước khi có kết quả kiểm thử và phê duyệt phát hành.
