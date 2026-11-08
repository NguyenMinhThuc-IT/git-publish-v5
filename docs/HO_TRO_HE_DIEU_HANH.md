# Git Publish V5 — bằng chứng tương thích

## V5.0.1 — đang kiểm định

Windows setup nhắm Python ổn định 3.11–3.15; 3.14 có bằng chứng Windows từ V5.0.0.
3.11–3.13 và 3.15 chưa có kết quả Windows cho bản mới. 3.15 là thử nghiệm,
chưa công bố hỗ trợ. CI giữ 10 cấu hình cũ và thêm Windows 3.11–3.13/3.15;
lane 3.15 cho phép thất bại nếu runtime chưa thiết lập được, không được coi là PASS.
Bộ cài dò từng interpreter và ghim executable tuyệt đối. Xem [README](../README.md).
Linux/macOS installer không thay đổi. Các bảng phía dưới là bằng chứng audit lịch sử.

## Audit lịch sử 5.0.0rc1

Phiên kiểm tra 2026-11-07; phiên bản 5.0.0rc1.
Audit2 tiếp tục xác nhận Ubuntu offline, không có môi trường native mới.
PASS chỉ áp dụng phạm vi đã chạy. SKIPPED = có kiểm tra nhưng thiếu môi trường.
NOT TESTED = chưa xác minh trên nền tảng thật. FAIL = kiểm tra đã chạy còn lỗi.

| Môi trường | Tự động/offline | Hệ điều hành/GUI thực tế |
|---|---|---|
| Ubuntu 26.04.1 hiện tại, Python 3.14.4 | PASS: pytest, Git local, Bash installer | GUI/clipboard thật: NOT TESTED |
| Ubuntu Desktop V4 | Theo tài liệu cũ đã thử | Không dùng làm chứng nhận V5 |
| Ubuntu Server không GUI | PASS: test headless trên Ubuntu hiện tại | Ubuntu Server riêng: NOT TESTED |
| Ubuntu 24.04 container | SKIPPED: thiếu runtime | NOT TESTED |
| Ubuntu 26.04 container | SKIPPED: thiếu runtime | NOT TESTED |
| Debian | SKIPPED: thiếu runtime | NOT TESTED |
| Fedora | SKIPPED: thiếu runtime | NOT TESTED |
| Arch Linux | SKIPPED: thiếu runtime | NOT TESTED |
| Kali Linux | SKIPPED: thiếu runtime | NOT TESTED |
| macOS | PASS: Darwin installer giả lập và pbcopy mock trên Ubuntu | macOS/Bash 3.2 thật: NOT TESTED |
| Windows PowerShell 5.1 | PASS: review cấu trúc; runtime SKIPPED | CHƯA KIỂM THỬ TRÊN WINDOWS |
| Windows PowerShell 7 | PASS: review cấu trúc; runtime SKIPPED | CHƯA KIỂM THỬ TRÊN WINDOWS |
| Zsh | SKIPPED: không có runtime | NOT TESTED |
| Python 3.10–3.13 | Chưa có interpreter để chạy | NOT TESTED |

## Dependency theo nền tảng

Mọi hệ điều hành cần Python >=3.10, Git, GitHub CLI và đăng nhập gh khi dùng thật.
Installer không cài dependency.

Linux runner đã chuẩn bị lệnh apt (Ubuntu/Debian/Kali), dnf (Fedora) và pacman
(Arch) bên trong container. Chưa chạy nên chưa xác nhận package resolution/image.
macOS cần cung cấp python3/git/gh từ môi trường người dùng; installer dùng Bash,
không dùng Zsh để chạy script. Zsh chỉ cần thêm PATH trong profile.
Windows installer thử py -3, python3, python theo thứ tự và kiểm tra >=3.10.

## Clipboard

- Linux Wayland: wl-copy.
- Linux X11: xclip rồi xsel khi backend trước lỗi.
- Không có DISPLAY/Wayland: trả False, URL vẫn in terminal.
- macOS: pbcopy với UTF-8.
- Windows: clip với dữ liệu UTF-16LE.
- Backend OS được mock trong test; chưa xác nhận GUI/clipboard thật.

## Chạy matrix khi có môi trường

~~~bash
python3 -B tools/linux_matrix.py --list
python3 -B tools/linux_matrix.py --run all --report dist/linux-matrix.json
~~~

Chỉ chạy nếu Docker/Podman có sẵn và runtime info truy cập được.
Không tự sudo/cài runtime. Cần mạng để tải image/dependency.
Nguồn mount readonly, test Git/installer ghi vào thư mục tạm trong container,
không gắn Git config/credentials host. Mỗi distro chạy pytest, import và launcher.
Tag rolling/latest có thể thay đổi; cần lưu log và image digest khi kiểm định phát hành.
Container không thay thế thử nghiệm Desktop/Wayland/X11, Windows hay macOS thật.

Xem [báo cáo cuối](V5_FINAL_REPORT.md) cho kết quả và giới hạn cụ thể.
