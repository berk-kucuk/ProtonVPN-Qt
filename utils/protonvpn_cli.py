"""ProtonVPN CLI wrapper.

Bu proje ProtonVPN'yi sistemde kurulu CLI aracı üzerinden yönetir.
CLI binary adı dağıtıma göre değişebildiği için (protonvpn / protonvpn-cli vb.)
tek bir noktadan tespit edip QProcess ile çalıştırırız.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Iterable, Optional


DEFAULT_CANDIDATES: tuple[str, ...] = (
    "protonvpn",
    "protonvpn-cli",
    "protonvpn-cli-ng",
)


@dataclass(frozen=True)
class ProtonVpnCli:
    executable: str

    @staticmethod
    def detect(explicit: Optional[str] = None) -> Optional["ProtonVpnCli"]:
        """Sistemdeki ProtonVPN CLI executable'ını bul."""
        if explicit:
            resolved = shutil.which(explicit)
            return ProtonVpnCli(resolved) if resolved else None

        for candidate in DEFAULT_CANDIDATES:
            resolved = shutil.which(candidate)
            if resolved:
                return ProtonVpnCli(resolved)
        return None

    def build_args(self, args: Iterable[str]) -> list[str]:
        return list(args)

