# Quyết định giấy phép — 5.0.0rc1

**CHƯA QUYẾT ĐỊNH.** LICENSE vẫn trống. Tài liệu này không cấp quyền hoặc áp dụng
bất kỳ giấy phép nào; chủ dự án cần phê duyệt sau khi xác nhận quyền đối với mã nguồn.

## Khi chưa có giấy phép

Đưa source lên mạng không tự cấp quyền sửa và phân phối lại. GitHub giải thích rằng
khi không có license, quyền tác giả mặc định vẫn áp dụng; việc xem/fork repository
Public theo điều khoản GitHub không thay cho giấy phép phần mềm.
[Nguồn: GitHub Docs](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

Vì vậy mục tiêu chia sẻ rộng rãi cần có điều khoản quyền sử dụng rõ ràng trước
phát hành. Bản ZIP hiện chỉ là ứng viên kiểm định nội bộ.

## Phương án để chủ dự án cân nhắc

| Phương án | Đặc điểm chính | Điều cần cân nhắc |
|---|---|---|
| MIT | Cho phép dùng, sửa, phân phối và thương mại; giữ thông báo quyền tác giả/permission | Ít nghĩa vụ phân phối; không bắt bản sửa phải mở mã |
| Apache-2.0 | Permissive, có cấp phép patent rõ ràng; giữ license/notices, ghi thay đổi; giữ NOTICE nếu áp dụng | Nhiều yêu cầu notice hơn MIT; cần xem điều khoản patent và nhãn hiệu |
| GPL-3.0 | Copyleft; phân phối tác phẩm thuộc phạm vi GPL phải đáp ứng điều kiện license và corresponding source | Phù hợp nếu muốn duy trì quyền sửa/chia sẻ cho người nhận; cần xem phạm vi tác phẩm kết hợp |
| Điều khoản khác hoặc chưa phát hành | Có thể cân nhắc nếu các quyền trên chưa đúng mong muốn | Không tự viết giấy phép độc quyền hoặc suy ra quyền từ mục tiêu chia sẻ |

Nguồn điều khoản cho từng dòng:
[MIT — OSI](https://opensource.org/license/mit),
[Apache License 2.0 — ASF](https://www.apache.org/licenses/LICENSE-2.0),
[GPL v3 — OSI](https://opensource.org/license/gpl-3.0).

Đây là tóm tắt phục vụ quyết định kỹ thuật/phân phối, không thay văn bản license
hoặc tư vấn pháp lý cho tình huống cụ thể. Không mặc định mọi dependency/công cụ
bên ngoài có cùng license với Git Publish; runtime hiện dùng Python stdlib và gọi
Git/gh được cài riêng, không nhúng binary của chúng vào ZIP.

## Thông tin cần xác nhận cuối

1. Quyền tác giả/chủ sở hữu và quyền phân phối mã nguồn hiện tại.
2. Muốn cho phép tích hợp vào sản phẩm đóng hay yêu cầu copyleft khi phân phối?
3. Có cần điều khoản patent/NOTICE hoặc nghĩa vụ với đóng góp bên ngoài?
4. Giấy phép được chọn, copyright holder và năm để điền LICENSE.
5. Phê duyệt scope phát hành, repository đích và thao tác công khai.

Chưa thực hiện bất kỳ lựa chọn hoặc thay đổi LICENSE nào trong phiên tự chủ.
