"""Check runnable examples/links and version claims without relying on test counts."""

import re
from pathlib import Path

from src.gitpublish.config import APP_VERSION


ROOT = Path(__file__).resolve().parents[1]


def test_public_docs_use_the_rc_version_and_do_not_claim_full_support():
    for name in ("README.md", "docs/HUONG_DAN_SU_DUNG.md", "docs/HO_TRO_HE_DIEU_HANH.md",
        "docs/V5_RELEASE_CHECKLIST.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert APP_VERSION in text, name
    support = (ROOT / "docs/HO_TRO_HE_DIEU_HANH.md").read_text(encoding="utf-8")
    assert "CHƯA KIỂM THỬ TRÊN WINDOWS" in support
    assert "macOS/Bash 3.2 thật: NOT TESTED" in support
    assert "SKIPPED: thiếu runtime" in support


def test_relative_markdown_links_resolve():
    for document in [ROOT / "README.md", *(ROOT / "docs").glob("*.md")]:
        text = document.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            assert (document.parent / target.split("#")[0]).exists(), (document.name, target)


def test_documented_installers_and_tools_exist():
    for name in ("installers/install.sh", "installers/install-macos.sh", "installers/install.ps1",
        "tools/linux_matrix.py", "tools/build_snapshot.py", "publish.py"):
        assert (ROOT / name).is_file()
