"""Terminal launcher helpers (cross-distro friendly)."""

from __future__ import annotations

import shutil
from typing import List, Optional, Sequence, Tuple


def _first_available(candidates: Sequence[str]) -> Optional[str]:
    for c in candidates:
        p = shutil.which(c)
        if p:
            return p
    return None


def linux_terminal_command() -> Optional[Tuple[str, List[str]]]:
    """Best-effort terminal command for Linux desktops.

    Returns (exe, args_prefix) where args_prefix expects the actual command appended.
    """
    # Debian/Ubuntu alternatives
    exe = _first_available(["x-terminal-emulator"])
    if exe:
        return (exe, ["-e"])

    # Common terminals
    exe = _first_available(["gnome-terminal"])
    if exe:
        # gnome-terminal wants '--' before command
        return (exe, ["--"])

    exe = _first_available(["konsole"])
    if exe:
        return (exe, ["-e"])

    exe = _first_available(["xfce4-terminal"])
    if exe:
        return (exe, ["-e"])

    exe = _first_available(["kitty"])
    if exe:
        return (exe, ["-e"])

    exe = _first_available(["alacritty"])
    if exe:
        return (exe, ["-e"])

    return None

