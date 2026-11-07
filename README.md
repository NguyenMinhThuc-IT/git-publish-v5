# Git Publish V5 — 5.0.0rc1

CLI Python giúp chuẩn bị và đưa dự án lên GitHub qua Git và GitHub CLI.

Đây là mã nguồn ứng viên phát hành đang được kiểm định, chưa phát hành công khai.
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

- Python 3.10 trở lên, Git và GitHub CLI (gh).
- Khi sử dụng GitHub thật: đăng nhập trước bằng gh auth login.
- Runtime Python chỉ dùng thư viện chuẩn; requirements.txt không có dependency.
- Chạy test cần pytest đã cài. Installer không tự cài dependency hoặc đăng nhập.

## Cài đặt

Giải nén ZIP nguồn hoặc dùng bản nguồn đã được kiểm tra. Giữ nguyên thư mục nguồn
sau khi cài: launcher tham chiếu trực tiếp tới publish.py.

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

Windows (đã kiểm thử trên GitHub Actions và publish thực tế):

~~~powershell
cd "C:\duong dan\git-publish"
.\installers\install.ps1
~~~

Cần Windows PowerShell 5.1 hoặc PowerShell 7 và chính sách cho phép chạy script.
Bộ cài tạo publish.ps1/publish.cmd trong $HOME\.local\bin, backup bản cũ
và thêm User PATH. Mở terminal mới sau cài. Không tự đổi execution policy.
Có thể dùng -BinDir với thư mục riêng và -NoPathUpdate để bỏ qua cập nhật PATH.
Launcher CMD cũng gọi PowerShell, nên vẫn chịu chính sách script.

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
Remote origin của workspace hiện không phải đích phát hành Git Publish.
