# Bảo mật và giới hạn — 5.0.0rc1

## Trước khi publish

Kiểm tra đúng thư mục root/branch, owner, origin fetch/push, visibility và tên file
trong preview. Mặc định Private; bỏ bảo vệ file cần xác nhận. Không nhập credentials
vào repository URL. Không chia sẻ output Git config chứa credentials.

Scanner CLI xét tên/đuôi/đường dẫn, không đọc giá trị bí mật. Có filesystem, index
và reachable history. Bảo vệ các dạng .env, key/cert, tên credentials/secrets trong
cấu hình, .aws/.ssh/.gnupg và .netrc/.npmrc/.pypirc. Không đi vào thư mục nhạy cảm
đã phát hiện hoặc metadata .git. Chọn bảo vệ giữ file local và bỏ tracking.

## Lịch sử và dữ liệu local

File được chọn còn trong lịch sử sẽ chặn publish, kể cả file đã xóa khỏi working tree.
.gitignore không xóa commit cũ. Nếu credentials từng bị công khai, cần thu hồi/đổi
ở nhà cung cấp và xử lý lịch sử theo quy trình riêng. Git Publish không tự sửa lịch sử.

Fast-forward có xác nhận và dùng --no-overwrite-ignore để không ghi đè file ignored
trùng đường dẫn. Lịch sử phân nhánh bị chặn. Remote thay đổi sau prepare vẫn phải
qua push thường; bị reject thì dừng. Không force push hoặc tự retry bằng thao tác phá hủy.

Hủy sau stage giữ staging area. Commit/repository đã tạo trước lỗi mạng không được
tự xóa. Kiểm tra trạng thái trước khi chạy lại. Không tự bỏ qua hooks/chính sách hệ thống.

## Audit artifact

ZIP và matrix dùng chung allowlist, loại .git/cache/backup/credentials theo tên,
symlink file/thư mục cha và đường dẫn không an toàn. Quét cục bộ thêm các mẫu
khóa riêng, GitHub token và AWS access key ID biết trước trong source được chọn.
Kết quả chỉ chứa đường dẫn, dòng và rule ID; không chứa chuỗi khớp.

~~~bash
python3 -B tools/build_snapshot.py --audit
~~~

Build/verify ZIP và staging container sẽ bị chặn nếu có mẫu khớp. Đây không phải
secret scanner toàn diện: không phát hiện mọi provider, dữ liệu mã hóa, chuỗi tách
nhỏ hoặc token định dạng tùy ý. Không đưa secrets thật vào test fixtures hoặc báo cáo.
Không upload mã hoặc credentials sang dịch vụ bên ngoài để kiểm tra.

Manifest/CRC/SHA-256 kiểm tra tính toàn vẹn, không phải chữ ký tác giả hay bằng chứng
không có mọi loại secrets. Cần review nội dung và quyền phân phối trước chia sẻ.

## Báo lỗi an toàn

Chuẩn bị phiên bản, OS, Git/Python/gh và bước tái hiện bằng dữ liệu giả. Bỏ giá trị
credentials, token, private URL có userinfo và nội dung file bí mật khỏi log.
Không dùng repository thật để tái hiện push phá hủy; dùng bare repository local tạm.
