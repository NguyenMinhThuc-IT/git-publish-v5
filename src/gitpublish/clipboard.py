"""Cross-platform clipboard support."""

import os
import shutil
import subprocess
import sys


def _copy(command, text):
    """Copy text using an operating-system clipboard command."""
    try:
        result = subprocess.run(
            command,
            input=text.encode("utf-16le" if command[0] == "clip" else "utf-8"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def copy_to_clipboard(text):
    """Copy text to the local machine's clipboard.

    Returns True on success, False otherwise.
    """
    commands = []

    if sys.platform == "darwin":
        commands.append(["pbcopy"])
    elif sys.platform == "win32":
        commands.append(["clip"])
    else:
        if os.environ.get("WAYLAND_DISPLAY"):
            commands.append(["wl-copy"])
        if os.environ.get("DISPLAY"):
            commands.extend([
                ["xclip", "-selection", "clipboard"],
                ["xsel", "--clipboard", "--input"],
            ])

    for command in commands:
        if shutil.which(command[0]) and _copy(command, text):
            return True

    return False
