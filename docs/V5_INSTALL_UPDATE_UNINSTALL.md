# Cài đặt, cập nhật và gỡ Git Publish — 5.0.0rc1

RC nội bộ, chưa phê duyệt phân phối công khai. Xem [hỗ trợ nền tảng](HO_TRO_HE_DIEU_HANH.md).
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
cd "/duong dan/git-publish-5.0.0rc1"
bash installers/install.sh
export PATH="$HOME/.local/bin:$PATH"
~~~

Giữ dòng PATH trong ~/.bashrc nếu dùng Bash tương tác và thư mục chưa có trong PATH.
Giữ thư mục nguồn: launcher tham chiếu publish.py tại đó. Không cần sudo.

## macOS — NOT TESTED native

Cung cấp python3, Git, gh trước, có thể từ Homebrew do người dùng quản lý.
Installer kiểm tra phiên bản Python và không tự cài Homebrew hoặc package.

~~~bash
cd "/duong dan/git-publish-5.0.0rc1"
bash installers/install-macos.sh
export PATH="$HOME/.local/bin:$PATH"
~~~

Với Zsh, lưu PATH vào ~/.zshrc. Script installer chạy bằng Bash, không chạy bằng
source trong Zsh. pbcopy có kiểm thử mock; macOS/Bash 3.2 thật chưa xác minh.

## Windows — CHƯA KIỂM THỬ TRÊN WINDOWS

PowerShell 5.1 hoặc 7; Git, gh và Python >=3.10 có sẵn. Installer thử py -3,
python3 rồi python; không tự thay execution policy.

~~~powershell
cd "C:\duong dan\git-publish-5.0.0rc1"
.\installers\install.ps1
~~~

CMD có thể gọi bộ cài bằng powershell.exe -NoProfile -File với đường dẫn được quote.
Cần chính sách cho phép script. Mở terminal mới rồi dùng publish.cmd từ CMD hoặc
PowerShell; publish.ps1 cũng có sẵn. CMD launcher vẫn chịu policy PowerShell.

Cài vào thư mục riêng và không sửa User PATH:

~~~powershell
.\installers\install.ps1 -BinDir "C:\Users\ten\Tools\GitPublish" -NoPathUpdate
~~~

## Cập nhật và khôi phục

1. Kiểm tra ZIP mới và giải nén vào thư mục khác; giữ nguyên nguồn cũ.
2. Chạy installer của bản mới. Launcher cũ được sao lưu trước thay thế.
3. Kiểm tra launcher/PATH và phiên bản trong header ở lần sử dụng tiếp theo.
   Không dùng dự án thật để thử push nếu chưa muốn publish.
4. Nếu lỗi, dừng và phục hồi launcher từ backup hoặc chạy lại installer của nguồn cũ.
5. Chỉ dọn nguồn/backup cũ sau khi xác minh launcher không còn trỏ tới chúng.

Linux/macOS dùng launcher tại ~/.local/bin/publish; backup có dạng publish.backup.*.
Windows có hai launcher và hai backup riêng: phải phục hồi cả publish.ps1/publish.cmd.
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
Rename-Item -LiteralPath (Join-Path $HOME ".local\bin\publish.ps1") -NewName "publish.ps1.disabled"
Rename-Item -LiteralPath (Join-Path $HOME ".local\bin\publish.cmd") -NewName "publish.cmd.disabled"
~~~

Giữ source và backup cho tới khi chắc chắn không cần khôi phục.
Chỉ bỏ mục PATH khi đó là thư mục dành riêng cho Git Publish; ~/.local/bin thường
được nhiều công cụ dùng chung. Windows có thể chỉnh User PATH qua giao diện Environment
Variables; không xóa cả PATH. Việc gỡ công cụ không yêu cầu xóa .git, gh auth hoặc dự án đã publish.
