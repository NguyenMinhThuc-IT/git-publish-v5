# Hướng dẫn Git Publish V5 — 5.0.0rc1

## Chuẩn bị và cài đặt

Python >=3.10, Git và GitHub CLI phải có sẵn trong PATH.
Không có thư viện Python bên thứ ba cho runtime.

~~~bash
python3 --version
git --version
gh --version
gh auth status
~~~

Windows: dùng py -3 --version hoặc python --version.
Đăng nhập GitHub khi muốn sử dụng thật: gh auth login.

Xem [README](../README.md) để cài Linux/macOS/Windows.
Quy trình thay phiên bản và khôi phục: [cập nhật/gỡ cài](V5_INSTALL_UPDATE_UNINSTALL.md).
Giới hạn quét và đóng gói: [bảo mật](V5_SECURITY.md).
Giữ thư mục nguồn ở nguyên vị trí. Nếu di chuyển hoặc thay Python, chạy lại installer.
Launcher cũ được backup trước thay thế; có thể phục hồi thủ công sau khi kiểm tra.
Linux/macOS không tự sửa PATH. Windows mặc định chỉ sửa User PATH.

## Quy trình publish

1. Vào thư mục gốc của dự án. Không chạy từ subdirectory, bare repo hoặc detached HEAD.
2. Chạy publish (publish.cmd trên Windows nếu muốn chọn launcher rõ ràng).
3. Repo mới: nhập tên hợp lệ, chọn Public/Private; Enter mặc định Private.
4. Repo có origin: tự lấy tên và giữ visibility; chặn tài khoản/remote khác đích.
5. Chọn bảo vệ: Enter chọn tất cả; số chọn từng mục; 0 bỏ bảo vệ với xác nhận rủi ro.
6. Kiểm tra preview và xác nhận. Chỉ hỏi commit message khi có thay đổi staged.
7. Ứng dụng xác minh visibility và lịch sử trước push. Nếu local bị chậm,
   chỉ fast-forward khi đồng ý. Lịch sử phân nhánh sẽ dừng để xử lý thủ công.
8. Sau thành công, URL được in; tùy lựa chọn để copy/mở trình duyệt.

[Y/n]: Enter đồng ý; [y/N]: Enter từ chối.
Ctrl+C trả mã 130. EOF kết thúc với mã 1, không tự đồng ý.
Hủy trước commit trả mã 0 và giữ staging area.
Hủy sau khi đã commit/khởi tạo/tạo repo không tự xóa những thay đổi đó.

## Troubleshooting

### Không thấy lệnh publish hoặc thiếu công cụ

Kiểm tra Python/Git/gh và PATH. Linux/macOS: command -v publish.
Windows: Get-Command publish -All, mở terminal mới sau cài.
Không xóa launcher backup trước khi xác minh bản mới.

### PowerShell chặn script

Bộ cài và launcher không tự bypass execution policy. CMD launcher cũng gọi script
PowerShell. Dùng quy trình cho phép script của tổ chức hoặc liên hệ quản trị viên;
không cần cấp quyền quản trị cho thư mục cài mặc định.
Windows thực tế vẫn CHƯA KIỂM THỬ TRÊN WINDOWS.

### Origin khác đích hoặc URL push khác fetch

~~~bash
git remote -v
git config --get-all remote.origin.url
git config --get-all remote.origin.pushurl
~~~

Không công bố output nếu URL chứa credentials. Xác minh đích với chủ dự án.
Git Publish không tự sửa origin. Chỉ hỗ trợ github.com qua HTTPS, SSH scp-style
và ssh://git@github.com/owner/repo.git. Không hỗ trợ GitHub Enterprise
hoặc publish vào owner khác tài khoản đăng nhập trong RC này.

### Mạng lỗi, xác thực, timeout hoặc push rejected

Kiểm tra kết nối, quyền tài khoản và gh auth status.
Lỗi tra repo ngoài HTTP 404 sẽ dừng; không coi mọi lỗi là repo mới.
Kiểm tra HEAD/status trước khi chạy lại; commit có thể đã được tạo trước lỗi push.
Không force push để vượt qua lỗi. Ứng dụng không in thành công khi push thất bại.

### Fast-forward bị chặn vì file local bị ignore

Remote có thể chứa file trùng đường dẫn với dữ liệu local đang bị ignore.
Git Publish dừng bằng --no-overwrite-ignore để giữ file đó. Sao lưu/đổi vị trí dữ liệu
local theo lựa chọn của bạn rồi kiểm tra lại; không tự xóa file để vượt qua thông báo.

### Lịch sử phân nhánh, detached HEAD, sai thư mục

~~~bash
git status -sb
git branch --show-current
git rev-parse --show-toplevel
git log --oneline --graph --left-right HEAD...FETCH_HEAD
~~~

Lệnh log cuối cần FETCH_HEAD đã được tạo bởi fetch. Sao lưu và xử lý lịch sử
thủ công theo quy trình dự án. Vào đúng root/branch trước chạy lại.

### Bí mật đã tracked hoặc đã xóa nhưng còn trong lịch sử

Chọn bảo vệ không xóa file local. .gitignore không xóa lịch sử.
Chương trình kiểm tra cả tên file đã bị xóa trong reachable history, chặn đường dẫn
được chọn còn trong lịch sử. Nếu đã lộ thông tin xác thực, thu hồi/đổi credentials
và xử lý lịch sử riêng; không đưa giá trị thật vào log hoặc báo cáo.
Không bảo đảm tìm được bí mật trong nội dung file tên bình thường.

### Clipboard hoặc trình duyệt không hoạt động

Wayland dùng wl-copy; X11 dùng xclip/xsel; macOS dùng pbcopy; Windows dùng clip.
Linux không DISPLAY/WAYLAND_DISPLAY trả URL qua terminal.
Không cài công cụ clipboard tự động. Copy thủ công URL khi tiện ích thiếu/lỗi.
Các backend macOS/Windows mới được kiểm thử mô phỏng trong phiên V5 này.

### Tên file đặc biệt, symlink, quyền ghi

Dấu cách/Unicode được bao phủ trong test Ubuntu. Tên chứa xuống dòng/NUL không
được thêm vào ignore; .gitignore symlink bị chặn để không ghi file bên ngoài.
Kiểm tra quyền thư mục khi installer lỗi; không dùng sudo để chạy bộ cài người dùng.

## Kiểm tra sau publish thực tế

~~~bash
git status -sb
git log -3 --oneline
git remote -v
git ls-files
gh repo view --json name,isPrivate,url
~~~

Kiểm tra tên file, visibility và nội dung repo. Không in secrets trong output chia sẻ.
