"""Configuration handling for Backflip SSH tunneling service."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

DEFAULT_CONFIG_PATH = Path("/etc/backflip/config.yaml")
CONFIG_DIR = DEFAULT_CONFIG_PATH.parent
LOG_DIR = Path("/var/log/backflip")
LOG_FILE = LOG_DIR / "backflip.log"
SYSTEMD_UNIT_PATH = Path("/etc/systemd/system/backflip.service")


class ConfigurationError(Exception):
    """Raised when configuration data is invalid or missing."""


@dataclass(slots=True)
class ProxyMapping:
    """Represents a single forwarded connection."""

    local_port: int
    remote_host: str
    remote_port: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProxyMapping":
        try:
            local_port = int(data["local_port"])
            remote_host = str(data["remote_host"])
            remote_port = int(data["remote_port"])
        except KeyError as exc:  # pragma: no cover - defensive
            raise ConfigurationError(f"Missing proxy field: {exc}") from exc
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(f"Invalid proxy mapping values: {data}") from exc
        return cls(local_port=local_port, remote_host=remote_host, remote_port=remote_port)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "local_port": self.local_port,
            "remote_host": self.remote_host,
            "remote_port": self.remote_port,
        }


@dataclass(slots=True)
class BackflipConfig:
    """Top-level configuration model."""

    mode: str
    server_iran: str
    server_foreign: str
    tunnel_port: int
    proxies: List[ProxyMapping] = field(default_factory=list)
    mux: bool = True
    password: str | None = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackflipConfig":
        try:
            mode = str(data["mode"]).lower()
            server_iran = str(data["server_iran"])
            server_foreign = str(data["server_foreign"])
            tunnel_port = int(data["tunnel_port"])
        except KeyError as exc:  # pragma: no cover - defensive
            raise ConfigurationError(f"Missing config field: {exc}") from exc
        except (TypeError, ValueError) as exc:
            raise ConfigurationError("Invalid primary configuration values") from exc

        if mode not in {"direct", "reverse"}:
            raise ConfigurationError("mode must be either 'direct' or 'reverse'")

        proxies_raw = data.get("proxies", []) or []
        if not isinstance(proxies_raw, Iterable):  # pragma: no cover - defensive
            raise ConfigurationError("proxies must be a list")

        proxies = [ProxyMapping.from_dict(item) for item in proxies_raw]

        mux = bool(data.get("mux", True))
        password = data.get("password")
        if password is not None:
            password = str(password)

        return cls(
            mode=mode,
            server_iran=server_iran,
            server_foreign=server_foreign,
            tunnel_port=tunnel_port,
            proxies=proxies,
            mux=mux,
            password=password if password else None,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "server_iran": self.server_iran,
            "server_foreign": self.server_foreign,
            "tunnel_port": self.tunnel_port,
            "proxies": [proxy.to_dict() for proxy in self.proxies],
            "mux": self.mux,
            "password": self.password,
        }


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> BackflipConfig:
    """Load Backflip configuration from *path*."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Configuration file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid YAML in configuration: {exc}") from exc

    return BackflipConfig.from_dict(raw)


def save_config(config: BackflipConfig, path: Path = DEFAULT_CONFIG_PATH) -> None:
    """Persist *config* to *path* in YAML format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config.to_dict(), handle, sort_keys=False)


def ensure_log_directory(path: Path = LOG_DIR) -> None:
    """Make sure the logging directory exists with safe permissions."""
    path.mkdir(parents=True, exist_ok=True)
    # Owner read/write/execute, group/world read/execute only. Not fatal if chmod fails.
    try:
        path.chmod(0o755)
    except PermissionError:  # pragma: no cover - depends on runtime privileges
        pass


__all__ = [
    "BackflipConfig",
    "ConfigurationError",
    "DEFAULT_CONFIG_PATH",
    "LOG_DIR",
    "LOG_FILE",
    "ProxyMapping",
    "SYSTEMD_UNIT_PATH",
    "ensure_log_directory",
    "load_config",
    "save_config",
]
