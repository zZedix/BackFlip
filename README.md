# 🚀 Backflip Tunnel

<div align="center">

![Backflip Logo](https://img.shields.io/badge/Backflip-Tunnel-blue?style=for-the-badge&logo=python)

**A powerful and resilient SSH tunneling service for connecting between Iranian and foreign servers**

[![Python](https://img.shields.io/badge/Python-3.10+-green?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![SSH](https://img.shields.io/badge/SSH-Tunnel-orange?style=flat-square&logo=ssh)](https://openssh.org)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-20.04+-blue?style=flat-square&logo=ubuntu)](https://ubuntu.com)
[![Debian](https://img.shields.io/badge/Debian-11+-red?style=flat-square&logo=debian)](https://debian.org)

[🇮🇷 **Persian Documentation**](README-fa.md) | [📖 **English Documentation**](#)

</div>

---

## ✨ Key Features

- 🎯 **Easy Installation**: Interactive installer with comprehensive guide
- 🔄 **Dual Tunnel Modes**: Direct (`-L`) and reverse (`-R`) tunneling
- ⚡ **Resilient Connection**: Uses `autossh` with SSH multiplexing
- 🛠️ **Simple Management**: CLI management for logs, restart, and settings
- 📝 **YAML Configuration**: Settings stored in `/etc/backflip/config.yaml`
- 🔧 **Systemd Service**: Auto-start and service management
- 📊 **Structured Logging**: Logs in `/var/log/backflip/` and systemd journal
- 🔐 **SSH Key Support**: Secure authentication without passwords
- 🌐 **Multi-Platform**: Works on Ubuntu, Debian, and other Linux distributions

## 🚀 Quick Start

### 🎯 One-Line Installation (Recommended)

```bash
curl -sSfL https://raw.githubusercontent.com/zZedix/BackFlip/main/install.sh | sudo bash
```

**What this does:**
- ✅ Installs system dependencies (`python3`, `pip`, `autossh`, `openssh-client`)
- ✅ Creates Python virtual environment in `/opt/backflip`
- ✅ Downloads latest Backflip from GitHub
- ✅ Launches interactive configuration wizard
- ✅ Sets up systemd service for auto-start

> 💡 **Local Installation**: If you have a local clone, run `sudo bash install.sh` from the repository root.

### 🔧 Manual Installation

#### Step 1: Install System Dependencies

**For Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv autossh openssh-client
```

**For CentOS/RHEL/Fedora:**
```bash
# CentOS/RHEL
sudo yum install -y python3 python3-pip autossh openssh-clients

# Fedora
sudo dnf install -y python3 python3-pip autossh openssh-clients
```

**For Arch Linux:**
```bash
sudo pacman -S python python-pip autossh openssh
```

#### Step 2: Install Backflip

**Option A: From GitHub (Recommended)**
```bash
sudo pip3 install git+https://github.com/zZedix/BackFlip.git
```

**Option B: From Local Source**
```bash
git clone https://github.com/zZedix/BackFlip.git
cd BackFlip
sudo pip3 install .
```

#### Step 3: Run Configuration Wizard

```bash
sudo backflip-install
```

The wizard will:
- ✅ Check for required dependencies
- ✅ Prompt for tunnel mode (direct/reverse)
- ✅ Ask for server addresses
- ✅ Configure proxy mappings
- ✅ Set up SSH multiplexing
- ✅ Create systemd service
- ✅ Enable and start the service

#### Step 4: Manage the Service

```bash
backflip
```

Use the interactive menu to:
- 📊 View logs and status
- 🔄 Restart the tunnel
- ⚙️ Edit configuration
- 🔄 Update the service
- 🗑️ Uninstall Backflip

## ⚙️ Configuration File

The installer creates `/etc/backflip/config.yaml`. Example:

```yaml
mode: "direct"
server_iran: "iran.example.com"
server_foreign: "us.example.com"
tunnel_port: 443
proxies:
  - local_port: 8080
    remote_host: us.example.com
    remote_port: 8080
  - local_port: 8443
    remote_host: us.example.com
    remote_port: 8443
mux: true
```

### 📋 Parameter Description

| Parameter | Description |
|-----------|-------------|
| **mode** | `direct` forwards local ports to remote hosts via `-L`. `reverse` exposes local services remotely via `-R`. |
| **server_iran / server_foreign** | SSH endpoints (e.g., `user@host`). The service connects to the foreign host in direct mode and to the Iranian host in reverse mode. |
| **tunnel_port** | SSH port used for the main tunnel. |
| **proxies** | A list of port mappings. By default `remote_host` matches the foreign server you provided; edit the YAML if the destination lives elsewhere. |
| **mux** | Enables SSH ControlMaster to reuse a single TCP connection across mappings. |

> 💡 **Note**: Update the file manually or through `backflip` → **Edit Settings**. After changes, restart the service to apply them.

## 🔧 Service Anatomy

| Component | Path | Description |
|-----------|------|-------------|
| **Service File** | `/etc/systemd/system/backflip.service` | Systemd service file |
| **Main Execution** | `python -m backflip.tunnel /etc/backflip/config.yaml` | Service execution command |
| **Logs** | `/var/log/backflip/backflip.log` + `journalctl -u backflip` | Log files |
| **Control Path** | `/run/backflip/mux-%r@%h-%p` | SSH multiplexing control path |

### 🔐 Enabling SSH Multiplexing (mux) with SSH Keys

If you provide a password during installation, Backflip automatically sets `mux: false` to avoid ControlMaster prompts. To re-enable multiplexing with key-based authentication:

1. **Generate a key for the Backflip service user (root) on the Iran server**
   ```bash
   sudo ssh-keygen -t ed25519 -f /root/.ssh/backflip -N ''
   ```

2. **Install the public key on the foreign server**
   ```bash
   sudo ssh-copy-id -i /root/.ssh/backflip root@your-foreign-host
   ```

3. **Reference the key via `/root/.ssh/config`**
   ```ssh-config
   Host backflip-foreign
       HostName your-foreign-host
       User root
       IdentityFile /root/.ssh/backflip
   ```

4. **Update `/etc/backflip/config.yaml`**
   - Set `server_foreign: backflip-foreign`
   - Remove the `password` field (or set `password: null`)
   - Set `mux: true`

5. **Restart Backflip**
   ```bash
   sudo systemctl restart backflip
   ```

The tunnel now reuses a single SSH control socket and reconnects instantly without storing any password.

## 🛠️ Development

### Prerequisites
- Python 3.10+
- Git

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/zZedix/BackFlip.git
cd BackFlip

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Run the tunnel directly
python -m backflip.tunnel path/to/config.yaml
```

### Development Tools
- **Linting**: `ruff` or `flake8`
- **Testing**: `pytest` (if you add tests)
- **Type Checking**: `mypy`

## 🗑️ Uninstalling

### Method 1: Using CLI (Recommended)
```bash
backflip
# Then select "Uninstall" option
```

### Method 2: Manual Removal
```bash
# Stop and disable service
sudo systemctl disable --now backflip

# Remove service file
sudo rm /etc/systemd/system/backflip.service

# Remove configuration and logs
sudo rm -rf /etc/backflip /var/log/backflip

# Remove Python package
sudo pip3 uninstall backflip

# Reload systemd
sudo systemctl daemon-reload
```

## 🏗️ Architecture

```
backflip/
├── __init__.py           # Package initialization
├── cli.py                # Command-line interface
├── config.py             # Configuration management
└── tunnel.py             # SSH tunnel implementation
scripts/
├── __init__.py
└── install.py            # Installation wizard
install.sh                # One-line installation script
pyproject.toml            # Project configuration
README.md / README-fa.md  # Documentation
LICENSE                   # MIT License
```

## 🤝 Contributing

We welcome contributions to Backflip Tunnel! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation if needed
4. **Add tests for new functionality**
   ```bash
   pytest tests/
   ```
5. **Ensure all tests pass**
6. **Submit a pull request**

### Development Setup

```bash
# Clone the repository
git clone https://github.com/zZedix/BackFlip.git
cd BackFlip

# Install in development mode
pip install -e .

# Run tests
pytest tests/
```

## 💰 Donations

If you find Backflip Tunnel useful and want to support its development, consider making a donation:

### Cryptocurrency Donations

- **Bitcoin (BTC)**: `bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh`
- **Ethereum (ETH)**: `0x8Fb2c4AF74e072CefC14A4E9927a1F86F1cd492c`
- **Tron (TRX)**: `TD43B2eT7JC8upacMarcmBBGFkjy75QJHK`
- **USDT (BEP20)**: `0x8Fb2c4AF74e072CefC14A4E9927a1F86F1cd492c`
- **TON**: `UQAFTGSc2YRNGQwwuTyD0Q-eB7pB0BNG0yvx5jVYAJWFu-y6`

### Other Ways to Support

- ⭐ **Star the repository** if you find it useful
- 🐛 **Report bugs** and suggest improvements
- 📖 **Improve documentation** and translations
- 🔗 **Share with others** who might benefit

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Backflip Tunnel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## ⚠️ Disclaimer

**Important Legal Notice:**

- **Educational Purpose**: This software is provided for educational and research purposes only.
- **Legal Compliance**: Users are responsible for ensuring compliance with all applicable laws and regulations in their jurisdiction.
- **No Warranty**: The software is provided "as is" without any warranty or guarantee of functionality.
- **Security Notice**: While we strive to maintain security, users should implement additional security measures as appropriate for their use case.
- **Network Usage**: Users are responsible for ensuring their network usage complies with their ISP's terms of service and local regulations.
- **No Liability**: The developers and contributors are not liable for any misuse, damage, or legal issues arising from the use of this software.

**By using this software, you acknowledge that you have read and understood this disclaimer and agree to use the software at your own risk.**

---

<div align="center">

**Backflip is licensed under the MIT License** 📄

[![Made with ❤️](https://img.shields.io/badge/Made%20with-❤️-red?style=flat-square)](https://github.com/zZedix/BackFlip)

</div>