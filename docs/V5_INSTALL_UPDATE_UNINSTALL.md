# Cài đặt, cập nhật và gỡ Git Publish — 5.0.1

V5.0.1 đang kiểm định; V5.0.0 đã phát hành. Xem [hỗ trợ nền tảng](HO_TRO_HE_DIEU_HANH.md).
Các lệnh dưới đây là hướng dẫn để người dùng thực hiện, không phải thao tác đã chạy
trên Windows/macOS trong phiên kiểm định.

## Kiểm tra bản tải về

ZIP phải đi kèm SHA-256 từ nguồn tin cậy. Linux dùng sha256sum -c với sidecar;
macOS dùng shasum -a 256 rồi đối chiếu; Windows dùng Get-FileHash -Algorithm SHA256.
Checksum phát hiện thay đổi, không xác thực tác giả nếu ZIP và sidecar cùng bị thay.

Giải nén vào thư mục mới, không trộn vào bản cũ. Trong nguồn đã tin cậy, có thể dùng:

~~~bash
python3 -B tools/build_snapshot.py --verify /duong/dan/candidate.zip
~~~

Kiểm định đầy đủ từ ZIP tự tạo, nếu môi trường đã có pytest:

~~~bash
python3 -B tools/verify_release.py /duong/dan/candidate.zip \
  --checksum /duong/dan/candidate.zip.sha256 --report dist/verify-new.json
~~~

Verifier chạy mã kiểm thử từ archive. Chỉ dùng với artifact nguồn đã tin cậy.
Không cài dependency, không đăng nhập gh, không tạo repository GitHub.

## Linux

Cần Python >=3.10, Git, gh trong PATH; installer không cài những công cụ này.

~~~bash
cd "/duong dan/git-publish-5.0.1"
bash installers/install.sh
export PATH="$HOME/.local/bin:$PATH"
~~~

Giữ dòng PATH trong ~/.bashrc nếu dùng Bash tương tác và thư mục chưa có trong PATH.
Giữ thư mục nguồn: launcher tham chiếu publish.py tại đó. Không cần sudo.

## macOS — NOT TESTED native

Cung cấp python3, Git, gh trước, có thể từ Homebrew do người dùng quản lý.
Installer kiểm tra phiên bản Python và không tự cài Homebrew hoặc package.

~~~bash
cd "/duong dan/git-publish-5.0.1"
bash installers/install-macos.sh
export PATH="$HOME/.local/bin:$PATH"
~~~

Với Zsh, lưu PATH vào ~/.zshrc. Script installer chạy bằng Bash, không chạy bằng
source trong Zsh. pbcopy có kiểm thử mock; macOS/Bash 3.2 thật chưa xác minh.

## Windows — one-click setup V5.0.1

Giải nén ZIP rồi chạy setup.cmd. Setup kiểm tra Python ổn định 3.11–3.15, Git,
gh và winget; mọi cài đặt/cập nhật đều cần xác nhận. Không tự đăng nhập GitHub.
Python 3.15 vẫn thử nghiệm, chưa công bố hỗ trợ. Xem [README](../README.md)
cho thứ tự chọn Python, nguồn tải chính thức và xử lý khi thiếu winget.

~~~powershell
cd "C:\duong dan\git-publish-5.0.1"
.\setup.cmd
~~~

Mã nguồn được lưu tại %LOCALAPPDATA%\GitPublish\releases\5.0.1-<id>;
mỗi lần cài tạo thư mục riêng, giữ mã nguồn/cấu hình cũ. Có thể xóa thư mục ZIP
đã giải nén sau khi hoàn tất. install-state.json trong thư mục ứng dụng ghi
Python tuyệt đối đã chọn; launcher sử dụng trực tiếp interpreter này.

Mở terminal mới rồi dùng publish trong PowerShell hoặc CMD. publish.cmd gọi
publish-runner.ps1 với policy Bypass chỉ trong tiến trình con, không thay
execution policy User/Machine; Group Policy của tổ chức vẫn có hiệu lực.
Bộ cài V5.0.1 cần xác minh Windows mới, tách biệt kết quả Windows V5.0.0.

Cài vào thư mục riêng và không sửa User PATH:

~~~powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\installers\setup-windows.ps1 -BinDir "C:\Users\ten\Tools\GitPublish" -NoPathUpdate
~~~

Installer trực tiếp installers/install.ps1 vẫn dành cho máy đã đủ dependency,
nhận -PythonPath để chọn interpreter và tham chiếu thư mục nguồn tại chỗ.

## Cập nhật và khôi phục

1. Kiểm tra ZIP mới và giải nén vào thư mục khác; giữ nguyên nguồn cũ.
2. Chạy installer của bản mới (Windows: setup.cmd). Launcher cũ được sao lưu trước thay thế.
3. Kiểm tra launcher/PATH và phiên bản trong header ở lần sử dụng tiếp theo.
   Không dùng dự án thật để thử push nếu chưa muốn publish.
4. Nếu lỗi, dừng và phục hồi launcher từ backup hoặc chạy lại installer của nguồn cũ.
5. Chỉ dọn nguồn/backup cũ sau khi xác minh launcher không còn trỏ tới chúng.

Linux/macOS dùng launcher tại ~/.local/bin/publish; backup có dạng publish.backup.*.
Windows V5.0.1: phục hồi đồng bộ publish-runner.ps1/publish.cmd từ cùng lần backup.
Khi quay về V5.0.0: khôi phục publish.ps1/publish.cmd cũ từ backup tương ứng;
các thư mục releases cũ được giữ lại trong LocalAppData để phục hồi.
Không chạy đồng thời hai installer. Không thay nội dung Git repository dự án khi cập nhật công cụ.

## Gỡ cài đặt mà giữ dữ liệu

Xác minh đường dẫn bằng command -v publish (Linux/macOS) hoặc
Get-Command publish -All (PowerShell). Launcher có thể thuộc ứng dụng khác nếu PATH trùng tên.

Linux/macOS: đổi tên launcher để vô hiệu hóa, dùng tên đích chưa tồn tại:

~~~bash
mv -i "$HOME/.local/bin/publish" "$HOME/.local/bin/publish.disabled"
~~~

Windows: vô hiệu hóa cả hai launcher; Rename-Item sẽ báo lỗi nếu tên mới đã tồn tại:

~~~powershell
Rename-Item -LiteralPath (Join-Path $HOME ".local\bin\publish-runner.ps1") -NewName "publish-runner.ps1.disabled"
Rename-Item -LiteralPath (Join-Path $HOME ".local\bin\publish.cmd") -NewName "publish.cmd.disabled"
~~~

Giữ source và backup cho tới khi chắc chắn không cần khôi phục.
Chỉ bỏ mục PATH khi đó là thư mục dành riêng cho Git Publish; ~/.local/bin thường
được nhiều công cụ dùng chung. Windows có thể chỉnh User PATH qua giao diện Environment
Variables; không xóa cả PATH. Việc gỡ công cụ không yêu cầu xóa .git, gh auth hoặc dự án đã publish.
