"""Docker-backed isolated command runner with bounded output capture.

Use a reviewed, pinned image and harden the Docker daemon/host. No host paths
are mounted by default. This is defense-in-depth, not a proof against escapes.
"""
from __future__ import annotations

import shutil
import subprocess
import threading
import time
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
    """Run argv in a constrained Docker container with no network or host mounts."""

    def __init__(
        self, image: str, *, docker_executable: str = "docker",
        memory: str = "256m", cpus: str = "1.0", pids_limit: int = 64,
        tmpfs_size: str = "64m", default_timeout_seconds: float = 10.0,
        max_output_bytes: int = 64_000,
    ) -> None:
        if not image or any(ch.isspace() for ch in image):
            raise ValueError("image must be a non-empty image reference without whitespace")
        if pids_limit < 1 or default_timeout_seconds <= 0 or max_output_bytes < 1:
            raise ValueError("resource limits must be positive")
        self.image, self.docker_executable = image, docker_executable
        self.memory, self.cpus, self.pids_limit, self.tmpfs_size = memory, cpus, pids_limit, tmpfs_size
        self.default_timeout_seconds, self.max_output_bytes = default_timeout_seconds, max_output_bytes

    def run(self, command: Sequence[str], *, input_text: str | None = None,
            timeout_seconds: float | None = None) -> SandboxResult:
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
            process = subprocess.Popen(
                argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=False, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
            )
        except OSError as exc:
            raise SandboxError(f"Unable to start Docker sandbox: {exc}") from exc

        lock = threading.Lock()
        captured = {"size": 0, "truncated": False}
        output = {"stdout": bytearray(), "stderr": bytearray()}

        def drain(name, stream):
            while True:
                chunk = stream.read(4096)
                if not chunk:
                    break
                with lock:
                    remaining = max(0, self.max_output_bytes - captured["size"])
                    if remaining:
                        kept = chunk[:remaining]
                        output[name].extend(kept)
                        captured["size"] += len(kept)
                    if len(chunk) > remaining:
                        captured["truncated"] = True

        readers = [
            threading.Thread(target=drain, args=("stdout", process.stdout), daemon=True),
            threading.Thread(target=drain, args=("stderr", process.stderr), daemon=True),
        ]
        for thread in readers:
            thread.start()

        def write_input():
            try:
                if input_text is not None:
                    process.stdin.write(input_text.encode("utf-8"))
                    process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            finally:
                try:
                    process.stdin.close()
                except OSError:
                    pass

        writer = threading.Thread(target=write_input, daemon=True)
        writer.start()
        timed_out = False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            process.wait()
        writer.join(timeout=1)
        for thread in readers:
            thread.join(timeout=2)
        elapsed = time.monotonic() - started
        if timed_out:
            raise SandboxError(f"Sandbox command timed out after {timeout} seconds")
        return SandboxResult(
            process.returncode,
            output["stdout"].decode("utf-8", errors="replace"),
            output["stderr"].decode("utf-8", errors="replace"),
            captured["truncated"], elapsed,
        )
