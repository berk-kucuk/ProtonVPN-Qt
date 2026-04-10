"""Detect ProtonVPN CLI supported features/settings."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from typing import FrozenSet, Optional

from utils.protonvpn_cli import ProtonVpnCli


@dataclass(frozen=True)
class ProtonVpnFeatures:
    config_set_commands: FrozenSet[str]

    def supports_setting(self, name: str) -> bool:
        return name in self.config_set_commands


@lru_cache(maxsize=1)
def detect_features(explicit_exe: Optional[str] = None) -> ProtonVpnFeatures:
    cli = ProtonVpnCli.detect(explicit_exe)
    if not cli:
        return ProtonVpnFeatures(config_set_commands=frozenset())

    try:
        cp = subprocess.run(
            [cli.executable, "config", "set", "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=2.5,
            check=False,
        )
        out = cp.stdout or ""
    except Exception:
        out = ""

    # Lines look like: "  netshield                Configure NetShield ..."
    cmds = set(re.findall(r"^\s{2}([a-z0-9-]+)\s{2,}", out, flags=re.MULTILINE))
    return ProtonVpnFeatures(config_set_commands=frozenset(cmds))

