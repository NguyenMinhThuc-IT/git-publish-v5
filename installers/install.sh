#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$HOME/.local/bin"
TARGET="$BIN_DIR/publish"

case "$(uname -s)" in
    Linux)  PLATFORM="Linux" ;;
    Darwin) PLATFORM="macOS" ;;
    *)
        echo "❌ Hệ điều hành chưa được hỗ trợ bởi bộ cài này."
        exit 1
        ;;
esac

echo "========================================"
echo " Git Publish V5 - Installer"
echo " Platform: $PLATFORM"
echo "========================================"

if [[ ! -f "$ROOT_DIR/publish.py" ]]; then
    echo "❌ Không tìm thấy publish.py"
    exit 1
fi

for cmd in python3 git gh; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "❌ Thiếu: $cmd"
        echo "Hãy cài đặt trước khi tiếp tục."
        exit 1
    fi
    echo "✓ $cmd"
done

if ! python3 -c \
    'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'
then
    echo "❌ Yêu cầu Python 3.10 trở lên."
    exit 1
fi

mkdir -p "$BIN_DIR"

if [[ -d "$TARGET" ]]; then
    echo "❌ Launcher đích là thư mục. Đã dừng, không ghi đè."
    exit 1
fi

if [[ -e "$TARGET" || -L "$TARGET" ]]; then
    BACKUP="$TARGET.backup.$(date +%Y%m%d%H%M%S)-$$"
    cp -P "$TARGET" "$BACKUP"
    echo "✓ Đã sao lưu lệnh cũ: $BACKUP"
fi

TEMP_FILE="$(mktemp "$BIN_DIR/.publish.XXXXXXXX")"
trap 'rm -f "$TEMP_FILE"' EXIT

PYTHON_EXE="$(python3 -c 'import sys; print(sys.executable)')"
printf '#!/usr/bin/env bash\nexec %q -X utf8 %q "$@"\n' \
    "$PYTHON_EXE" "$ROOT_DIR/publish.py" > "$TEMP_FILE"

chmod +x "$TEMP_FILE"
mv -f "$TEMP_FILE" "$TARGET"

echo
echo "✅ Cài đặt lệnh publish thành công!"
echo "Vị trí: $TARGET"

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo
    echo "⚠ Cần thêm ~/.local/bin vào PATH."
    if [[ "$PLATFORM" == "macOS" ]]; then
        echo "Thêm dòng sau vào ~/.zshrc:"
    else
        echo "Thêm dòng sau vào cấu hình shell của bạn:"
    fi
    echo 'export PATH="$HOME/.local/bin:$PATH"'
fi

if ! gh auth status >/dev/null 2>&1; then
    echo
    echo "⚠ Chưa đăng nhập GitHub CLI."
    echo "Chạy: gh auth login"
fi

echo
echo "Sử dụng:"
echo "  cd /duong/dan/du-an"
echo "  publish"
echo
echo "V5 RC: xem docs/HO_TRO_HE_DIEU_HANH.md về phạm vi đã kiểm thử."
