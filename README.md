# ProtonVpn-Qt

A lightweight, modern PySide6 (Qt) desktop interface for the official Proton VPN Linux CLI.

This project provides a sleek, blurred UI with an animated background, designed to make managing your Proton VPN connection on Linux both functional and aesthetically pleasing.

-----

## Screenshots

| Status: Connected | Status: Disconnected |
| :---: | :---: |
| \<img src="path/to/connected.png" alt="Connected" width="400"\> | \<img src="path/to/disconnected.png" alt="Disconnected" width="400"\> |
| *Modern blur effects on server list and side panels.* | *Real-time status updates and clean UI.* |

-----

## Features

  * **Modern UI/UX:** Frosted glass (blur) effects on the server list and sidebar panels.
  * **Dynamic Adaptation:** Right toolbar buttons and settings automatically adjust based on detected CLI capabilities.
  * **Smart Discovery:** Auto-detects the CLI executable (protonvpn, protonvpn-cli, or protonvpn-cli-ng).
  * **CLI-First Authentication:** Handles the sign-in flow through your preferred terminal emulator.
  * **Performance:** Lightweight countries list with intelligent caching.
  * **Status Monitoring:** Real-time visual feedback on your VPN tunnel state.

-----

## Requirements

  * **OS:** Linux (X11/Wayland support)
  * **Python:** 3.x
  * **Proton VPN CLI:** Must be installed and accessible via PATH.

Verify your installation by running:

```bash
protonvpn --help
```

-----

## Getting Started

### Option 1: Standard Python Execution

If you have PySide6 installed in your environment:

```bash
python3 main.py
```

### Option 2: Nix (Declarative Environment)

If you prefer not to install dependencies globally, use the provided Nix shell:

```bash
nix-shell --run "python3 main.py"
```

-----

## Implementation Details

  * **Visual Architecture:** The UI utilizes semi-transparency. The server list panel and the icon panel on the right utilize blur effects to enhance readability against the animated background.
  * **Authentication:** The "Sign In" button triggers a terminal session. If no common terminal emulator is found, the app provides instructions for manual CLI login.
  * **Settings:** The interface only displays configuration options officially supported by the detected CLI version to ensure stability.

-----

## Disclaimer

This is an unofficial GUI and is not affiliated with, maintained, or endorsed by Proton AG. Use it at your own risk.
