"""Backflip tunnel supervisor and runtime."""
from __future__ import annotations

import asyncio
import logging
import os
import signal
import shutil
import sys
import time
from asyncio.subprocess import PIPE
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from .config import (
    BackflipConfig,
    DEFAULT_CONFIG_PATH,
    LOG_DIR,
    LOG_FILE,
    ProxyMapping,
    ensure_log_directory,
    load_config,
)

CONTROL_PATH_DIR = Path("/run/backflip")
CONTROL_PATH_TEMPLATE = str(CONTROL_PATH_DIR / "mux-%r@%h-%p")
DEFAULT_AUTOSSH_LOG = LOG_DIR / "autossh.log"
LOGGER_NAME = "backflip.tunnel"


class TunnelRuntimeError(RuntimeError):
    """Raised when the tunnel supervisor encounters unrecoverable issues."""


@dataclass(slots=True)
class TunnelCommand:
    """Represents a concrete SSH command for a proxy mapping."""

    label: str
    argv: List[str]


class TunnelSupervisor:
    """Launch and supervise SSH tunnel processes."""

    def __init__(self, config: BackflipConfig) -> None:
        self.config = config
        self.logger = logging.getLogger(LOGGER_NAME)
        self.stop_event = asyncio.Event()
        self.ssh_binary = self._required_binary("ssh")
        self.autossh_binary = self._optional_binary("autossh")
        ensure_log_directory(LOG_DIR)
        CONTROL_PATH_DIR.mkdir(parents=True, exist_ok=True)
        try:  # pragma: no cover - depends on runtime privileges
            CONTROL_PATH_DIR.chmod(0o700)
        except PermissionError:
            self.logger.warning("Unable to set permissions on %s", CONTROL_PATH_DIR)

    @staticmethod
    def _required_binary(name: str) -> str:
        path = shutil.which(name)
        if not path:
            raise TunnelRuntimeError(f"Required binary '{name}' not found in PATH")
        return path

    @staticmethod
    def _optional_binary(name: str) -> str | None:
        return shutil.which(name)

    def build_commands(self) -> List[TunnelCommand]:
        commands: List[TunnelCommand] = []
        target_host = self._target_host()

        for mapping in self.config.proxies:
            forward_flag, forward_spec = self._forward_args(mapping)
            forward_arg = f"{forward_flag}{forward_spec}"
            argv = self._base_ssh_arguments()
            argv.extend([forward_arg, target_host])
            label = f"{forward_flag} {forward_spec} -> {target_host}"
            commands.append(TunnelCommand(label=label, argv=argv))
        return commands

    def _target_host(self) -> str:
        return self.config.server_foreign if self.config.mode == "direct" else self.config.server_iran

    def _forward_args(self, mapping: ProxyMapping) -> tuple[str, str]:
        spec = f"{mapping.local_port}:{mapping.remote_host}:{mapping.remote_port}"
        if self.config.mode == "direct":
            return "-L", spec
        return "-R", spec

    def _base_ssh_arguments(self) -> List[str]:
        ssh_args: List[str] = [
            "-N",
            "-p",
            str(self.config.tunnel_port),
            "-o",
            "ServerAliveInterval=30",
            "-o",
            "ServerAliveCountMax=3",
            "-o",
            "ExitOnForwardFailure=yes",
            "-o",
            "StrictHostKeyChecking=accept-new",
        ]
        if self.config.mux:
            ssh_args.extend(
                [
                    "-o",
                    "ControlMaster=auto",
                    "-o",
                    f"ControlPath={CONTROL_PATH_TEMPLATE}",
                    "-o",
                    "ControlPersist=600",
                ]
            )

        if self.autossh_binary and not self.config.password:
            return [self.autossh_binary, "-M", "0", *ssh_args]
        return [self.ssh_binary, *ssh_args]

    async def run(self) -> None:
        commands = self.build_commands()
        if not commands:
            self.logger.warning("No proxy mappings configured; nothing to do")
            await self.stop_event.wait()
            return

        tasks = [asyncio.create_task(self._run_command(cmd)) for cmd in commands]
        try:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        finally:
            self.stop_event.set()
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_command(self, command: TunnelCommand) -> None:
        backoff = 5
        while not self.stop_event.is_set():
            argv = list(command.argv)
            env = os.environ.copy()
            if self.autossh_binary and not self.config.password:
                env.setdefault("AUTOSSH_GATETIME", "0")
                env.setdefault("AUTOSSH_LOGFILE", str(DEFAULT_AUTOSSH_LOG))
                env.setdefault("AUTOSSH_SSH", self.ssh_binary)
            if self.config.password:
                env.setdefault("SSHPASS", self.config.password)
                argv = ["sshpass", "-e", *argv]
            start_time = time.monotonic()
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=PIPE,
                stderr=PIPE,
                env=env,
            )
            self.logger.info("Started tunnel %s (pid=%s)", command.label, proc.pid)

            stdout_task = asyncio.create_task(self._pipe_to_logger(proc.stdout, logging.INFO, command.label))
            stderr_task = asyncio.create_task(self._pipe_to_logger(proc.stderr, logging.ERROR, command.label))
            stop_task = asyncio.create_task(self.stop_event.wait())
            wait_task = asyncio.create_task(proc.wait())

            done, _ = await asyncio.wait(
                {stop_task, wait_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            if stop_task in done:
                self.logger.info("Stopping tunnel %s", command.label)
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), timeout=10)
                except asyncio.TimeoutError:
                    self.logger.warning("Force killing tunnel %s", command.label)
                    proc.kill()
                    await proc.wait()
                stdout_task.cancel()
                stderr_task.cancel()
                await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
                break

            return_code = await wait_task
            stdout_task.cancel()
            stderr_task.cancel()
            await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)

            uptime = time.monotonic() - start_time
            if return_code == 0:
                self.logger.info("Tunnel %s exited cleanly after %.1fs", command.label, uptime)
            else:
                self.logger.warning(
                    "Tunnel %s exited with status %s after %.1fs",
                    command.label,
                    return_code,
                    uptime,
                )

            if self.stop_event.is_set():
                break

            if uptime >= 60:
                backoff = 5
                await asyncio.sleep(backoff)
            else:
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 300)

    async def _pipe_to_logger(self, stream: asyncio.StreamReader | None, level: int, label: str) -> None:
        if stream is None:
            return
        while not stream.at_eof():
            try:
                line = await stream.readline()
            except asyncio.CancelledError:  # pragma: no cover - cancellation path
                return
            if not line:
                break
            text = line.decode("utf-8", errors="replace").rstrip()
            if text:
                self.logger.log(level, "%s | %s", label, text)

    def request_shutdown(self) -> None:
        self.stop_event.set()


def setup_logging() -> None:
    ensure_log_directory(LOG_DIR)
    handlers: List[logging.Handler] = [
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=handlers,
    )


def _resolve_config_path(argv: Sequence[str]) -> Path:
    if not argv:
        return DEFAULT_CONFIG_PATH
    path = Path(argv[0]).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


async def _async_main(config_path: Path) -> None:
    config = load_config(config_path)
    supervisor = TunnelSupervisor(config)

    loop = asyncio.get_running_loop()
    for signame in {signal.SIGINT, signal.SIGTERM}:
        try:
            loop.add_signal_handler(signame, supervisor.request_shutdown)
        except NotImplementedError:  # pragma: no cover - platform dependent
            signal.signal(signame, lambda *_: supervisor.request_shutdown())

    await supervisor.run()


def main(argv: Sequence[str] | None = None) -> None:
    setup_logging()
    if argv is None:
        argv = sys.argv[1:]
    config_path = _resolve_config_path(list(argv))
    asyncio.run(_async_main(config_path))


if __name__ == "__main__":  # pragma: no cover
    main()
