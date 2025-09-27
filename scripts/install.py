"""Backflip installation wizard."""
from __future__ import annotations

import getpass
import os
import socket
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import questionary

SIMPLE_PROMPTS = bool(os.environ.get("BACKFLIP_SIMPLE_PROMPT")) or not (
    sys.stdin.isatty() and sys.stdout.isatty()
)

if __package__ is None or __package__ == "":  # pragma: no cover - executed when run as script
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backflip.config import (  # noqa: E402  - imported after sys.path tweak
    CONFIG_DIR,
    LOG_DIR,
    LOG_FILE,
    SYSTEMD_UNIT_PATH,
    BackflipConfig,
    ProxyMapping,
    ensure_log_directory,
    save_config,
)

SERVICE_NAME = "backflip"
SUPPORTED_PACKAGE_MANAGERS = (
    "apt-get",
    "dnf",
    "yum",
    "zypper",
    "pacman",
    "apk",
    "brew",
)

PACKAGE_MAP: Dict[str, Dict[str, List[str]]] = {
    "ssh": {
        "apt-get": ["openssh-client"],
        "dnf": ["openssh-clients"],
        "yum": ["openssh-clients"],
        "zypper": ["openssh"],
        "pacman": ["openssh"],
        "apk": ["openssh"],
        "brew": ["openssh"],
        "default": ["openssh"],
    },
    "autossh": {
        "apt-get": ["autossh"],
        "dnf": ["autossh"],
        "yum": ["autossh"],
        "zypper": ["autossh"],
        "pacman": ["autossh"],
        "apk": ["autossh"],
        "brew": ["autossh"],
        "default": ["autossh"],
    },
    "sshpass": {
        "apt-get": ["sshpass"],
        "dnf": ["sshpass"],
        "yum": ["sshpass"],
        "zypper": ["sshpass"],
        "pacman": ["sshpass"],
        "apk": ["sshpass"],
        "brew": ["sshpass"],
        "default": ["sshpass"],
    },
}


@dataclass(slots=True)
class PackageManager:
    name: str
    command: str


class InstallationError(RuntimeError):
    """Raised when installation steps fail."""


def ensure_root() -> None:
    if os.geteuid() != 0:
        raise InstallationError("Backflip installation must be run as root (try sudo).")


def detect_package_manager() -> PackageManager | None:
    for candidate in SUPPORTED_PACKAGE_MANAGERS:
        path = shutil.which(candidate)
        if path:
            return PackageManager(name=candidate, command=path)
    return None


def install_packages(manager: PackageManager, packages: Iterable[str]) -> None:
    packages = list(dict.fromkeys(packages))
    if not packages:
        return

    def run(cmd: List[str]) -> None:
        subprocess.run(cmd, check=True)

    if manager.name == "apt-get":
        run([manager.command, "update"])
        run([manager.command, "install", "-y", *packages])
    elif manager.name in {"dnf", "yum"}:
        run([manager.command, "install", "-y", *packages])
    elif manager.name == "zypper":
        run([manager.command, "refresh"])
        run([manager.command, "install", "-y", *packages])
    elif manager.name == "pacman":
        run([manager.command, "-Sy", "--noconfirm", *packages])
    elif manager.name == "apk":
        run([manager.command, "update"])
        run([manager.command, "add", *packages])
    elif manager.name == "brew":
        run([manager.command, "install", *packages])
    else:  # pragma: no cover - defensive
        raise InstallationError(f"Unsupported package manager: {manager.name}")


def ensure_dependency(binary: str) -> None:
    if shutil.which(binary):
        return

    manager = detect_package_manager()
    if not manager:
        raise InstallationError(
            f"Missing required dependency '{binary}' and no supported package manager was found."
        )

    package_names = PACKAGE_MAP.get(binary, {}).get(manager.name)
    if not package_names:
        package_names = PACKAGE_MAP.get(binary, {}).get("default", [binary])

    try:
        install_packages(manager, package_names)
    except subprocess.CalledProcessError as exc:
        raise InstallationError(f"Failed to install packages for {binary}: {exc}") from exc

    if not shutil.which(binary):
        raise InstallationError(
            f"Dependency '{binary}' is still missing after attempting installation."
        )


def ask_text(prompt: str, default: str | None = None) -> str:
    while True:
        if SIMPLE_PROMPTS:
            suffix = f" [{default}]" if default else ""
            try:
                value = input(f"{prompt}{suffix}: ")
            except EOFError as exc:
                raise InstallationError("Installation aborted by user.") from exc
            if not value and default is not None:
                return default
        else:
            question = questionary.text(prompt, default=default) if default else questionary.text(prompt)
            value = question.ask()
            if value is None:
                raise InstallationError("Installation aborted by user.")

        value = value.strip()
        if value:
            return value
        if default is not None:
            return default
        print("A value is required.")


def ask_port(prompt: str, default: int | None = None) -> int:
    while True:
        value = ask_text(prompt, default=str(default) if default is not None else None)
        try:
            port = int(value)
            if not (1 <= port <= 65535):
                raise ValueError
            return port
        except ValueError:
            print("Please enter a valid TCP port between 1 and 65535.")

def default_server_iran() -> str:
    override = os.environ.get("BACKFLIP_IRAN_ADDRESS")
    if override:
        return override
    user = os.environ.get("SUDO_USER") or getpass.getuser()
    hostname = socket.getfqdn() or socket.gethostname()
    return f"{user}@{hostname}"


def ask_mode() -> str:
    while True:
        value = ask_text("Backflip connection mode (direct/reverse)", default="direct").lower()
        if value in {"direct", "reverse"}:
            return value
        print("Please enter 'direct' or 'reverse'.")


def gather_proxy_ports() -> List[int]:
    while True:
        raw = ask_text("Proxy ports (comma-separated, leave blank for none)", default="")
        parts = [item.strip() for item in raw.split(",") if item.strip()]
        if not parts:
            return []
        try:
            ports = [int(item) for item in parts]
        except ValueError:
            print("Ports must be integers separated by commas.")
            continue
        invalid = [port for port in ports if not (1 <= port <= 65535)]
        if invalid:
            print("Ports must be between 1 and 65535.")
            continue
        return list(dict.fromkeys(ports))


def write_systemd_unit(python_exec: str) -> None:
    unit_contents = f"""[Unit]
Description=Backflip SSH tunneling service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={python_exec} -m backflip.tunnel {CONFIG_DIR / 'config.yaml'}
Restart=on-failure
RestartSec=5
User=root
Group=root
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    SYSTEMD_UNIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SYSTEMD_UNIT_PATH.write_text(unit_contents, encoding="utf-8")
    os.chmod(SYSTEMD_UNIT_PATH, 0o644)


def enable_service() -> None:
    systemctl = shutil.which("systemctl")
    if not systemctl:
        raise InstallationError("systemctl not found; systemd is required to manage Backflip service.")
    subprocess.run([systemctl, "daemon-reload"], check=True)
    subprocess.run([systemctl, "enable", "--now", SERVICE_NAME], check=True)


def create_config(config: BackflipConfig) -> None:
    ensure_log_directory(LOG_DIR)
    save_config(config)
    os.chmod(CONFIG_DIR, 0o750)
    os.chmod(CONFIG_DIR / "config.yaml", 0o640)


def run_installation() -> None:
    ensure_root()
    print("Checking system dependencies...")
    ensure_dependency("ssh")
    ensure_dependency("autossh")

    mode = ask_mode()
    foreign_host = ask_text("Foreign server IP or hostname")
    foreign_user = ask_text("SSH username for foreign server", default="root")
    tunnel_port = ask_port("SSH port on foreign server", default=22)
    proxy_ports = gather_proxy_ports()
    password = ask_text("SSH password (leave blank for key authentication)", default="")

    if password:
        ensure_dependency("sshpass")

    server_iran = default_server_iran()
    server_foreign = f"{foreign_user}@{foreign_host}"
    proxies = [
        ProxyMapping(
            local_port=port,
            remote_host=foreign_host,
            remote_port=port,
        )
        for port in proxy_ports
    ]
    mux_enabled = not password

    config = BackflipConfig(
        mode=mode,
        server_iran=server_iran,
        server_foreign=server_foreign,
        tunnel_port=tunnel_port,
        proxies=proxies,
        mux=bool(mux_enabled),
        password=password or None,
    )

    print("Writing configuration file...")
    create_config(config)

    print("Installing systemd service...")
    write_systemd_unit(sys.executable)

    print("Enabling service...")
    enable_service()

    print("Backflip installation completed successfully.")


def main() -> None:
    try:
        run_installation()
    except InstallationError as exc:
        print(f"Installation failed: {exc}")
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f"System command failed: {exc}")
        sys.exit(exc.returncode)


if __name__ == "__main__":  # pragma: no cover
    main()
