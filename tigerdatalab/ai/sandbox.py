"""Docker-backed isolated command runner for explicitly configured workloads.

This is a boundary for running untrusted snippets in a prebuilt container image,
not a general-purpose container orchestrator. Use a reviewed, pinned image and
harden the Docker daemon/host. No host paths are mounted by default.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from typing import Sequence


class SandboxError(RuntimeError):
    """Raised when isolated command execution fails or exceeds limits."""


@dataclass(frozen=True)
class SandboxResult:
    returncode: int
    stdout: str
    stderr: str
    truncated: bool
    elapsed_seconds: float


class DockerSandbox:
    """Run an argv command in a constrained Docker container with no network.

    The caller supplies an explicit executable and argument list; shell parsing
    is never used. The container gets no host mounts, no network, a read-only
    root filesystem, dropped Linux capabilities and bounded resources.
    """

    def __init__(
        self,
        image: str,
        *,
        docker_executable: str = "docker",
        memory: str = "256m",
        cpus: str = "1.0",
        pids_limit: int = 64,
        tmpfs_size: str = "64m",
        default_timeout_seconds: float = 10.0,
        max_output_bytes: int = 64_000,
    ) -> None:
        if not image or any(ch.isspace() for ch in image):
            raise ValueError("image must be a non-empty image reference without whitespace")
        if pids_limit < 1 or default_timeout_seconds <= 0 or max_output_bytes < 1:
            raise ValueError("resource limits must be positive")
        self.image = image
        self.docker_executable = docker_executable
        self.memory, self.cpus, self.pids_limit, self.tmpfs_size = memory, cpus, pids_limit, tmpfs_size
        self.default_timeout_seconds, self.max_output_bytes = default_timeout_seconds, max_output_bytes

    def run(
        self,
        command: Sequence[str],
        *,
        input_text: str | None = None,
        timeout_seconds: float | None = None,
    ) -> SandboxResult:
        import time
        if not command or any(not isinstance(part, str) or "\x00" in part for part in command):
            raise ValueError("command must be a non-empty sequence of NUL-free strings")
        executable = shutil.which(self.docker_executable)
        if executable is None:
            raise SandboxError("Docker executable not found; install Docker or use a managed isolated runner")
        timeout = self.default_timeout_seconds if timeout_seconds is None else timeout_seconds
        if timeout <= 0:
            raise ValueError("timeout_seconds must be positive")
        argv = [
            executable, "run", "--rm", "--network=none", "--read-only",
            "--cap-drop=ALL", "--security-opt=no-new-privileges",
            "--pids-limit", str(self.pids_limit), "--memory", self.memory,
            "--cpus", self.cpus, "--user", "65534:65534",
            "--tmpfs", f"/tmp:rw,noexec,nosuid,size={self.tmpfs_size}",
            "--workdir", "/tmp", "--pull=never", self.image, *command,
        ]
        started = time.monotonic()
        try:
            completed = subprocess.run(
                argv, input=input_text, text=True, capture_output=True,
                timeout=timeout, check=False, shell=False,
                env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
            )
        except subprocess.TimeoutExpired as exc:
            raise SandboxError(f"Sandbox command timed out after {timeout} seconds") from exc
        except OSError as exc:
            raise SandboxError(f"Unable to start Docker sandbox: {exc}") from exc
        elapsed = time.monotonic() - started
        stdout, stderr = completed.stdout or "", completed.stderr or ""
        combined = (stdout + stderr).encode("utf-8", errors="replace")
        truncated = len(combined) > self.max_output_bytes
        if truncated:
            clipped = combined[:self.max_output_bytes].decode("utf-8", errors="replace")
            stdout, stderr = clipped, ""
        return SandboxResult(completed.returncode, stdout, stderr, truncated, elapsed)
