"""Terminal UI helpers."""


def print_header(title: str) -> None:
    print()
    print("=" * 54)
    print(f"🚀 {title}")
    print("=" * 54)
    print()


def ask_text(message: str, required: bool = True) -> str:
    while True:
        value = input(message).strip()
        if value or not required:
            return value
        print("❌ Không được để trống.")


def ask_binary(message: str) -> bool:
    while True:
        value = input(message).strip()
        if value in ("1", "0"):
            return value == "1"
        print("❌ Chỉ được nhập 1 hoặc 0.")


def ask_yes_no(title: str) -> bool:
    print()
    print(title)
    print("1. Có")
    print("0. Không")
    return ask_binary("Chọn [1/0]: ")


def show_git_preview(
    staged_files: list[str],
    protected_files: list[str],
) -> None:
    print()
    print("=" * 54)
    print("🔍 GIT PREVIEW")
    print("=" * 54)

    print("\n🔒 Protected:")
    if protected_files:
        for path in protected_files:
            print(f"  ✓ {path}")
    else:
        print("  Không có mục nào được chọn.")

    print("\n📤 Staged changes:")
    if staged_files:
        for item in staged_files:
            print(f"  ✓ {item}")
    else:
        print("  Không có thay đổi mới để commit.")

    print("\n" + "=" * 54)


def confirm(message: str = "Tiếp tục publish?") -> bool:
    print(f"\n{message}")
    print("1. Tiếp tục")
    print("0. Hủy")

    return ask_binary("Chọn [1/0]: ")
