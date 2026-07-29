"""Windows -> WSL bridge.

Find_Orb has no supported Windows build (the project's own README says so: the Windows
build needs MFC and the Microsoft compiler, and only pre-built EXEs are offered). We build
and run the console binary ``fo`` under WSL and shell into it from Windows.

Everything here is about one problem: a path that Windows calls ``C:\\Users\\x`` is
``/mnt/c/Users/x`` inside WSL, and the two halves of this package have to agree on which
one they are holding.

On a non-Windows host the same functions degrade to running ``fo`` directly, so the module
is testable (and usable) without WSL.
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath

#: ``C:\\foo`` / ``c:/foo`` -> drive letter + remainder.
_DRIVE_RE = re.compile(r"^([A-Za-z]):[\\/](.*)$", re.DOTALL)

#: Where INSTALL.sh's build order leaves the console binary (``make install`` copies it to
#: ``$INSTALL_DIR/bin`` and ``INSTALL_DIR`` defaults to ``~``).
DEFAULT_FO = "$HOME/bin/fo"

#: Find_Orb's configuration + data directory, created by the install step.
DEFAULT_CONFIG_DIR = "$HOME/.find_orb"

ENV_FO = "ITF_LINKER_FO"
ENV_CONFIG = "ITF_LINKER_FO_CONFIG"


class WslError(RuntimeError):
    """Raised when the WSL bridge itself fails (as opposed to ``fo`` failing)."""


def on_windows() -> bool:
    return platform.system() == "Windows"


def to_wsl_path(path: str | os.PathLike[str]) -> str:
    """Translate a Windows path to its WSL ``/mnt/<drive>`` equivalent.

    Already-POSIX paths pass through unchanged, so this is safe to apply twice and safe to
    call on a Linux host.

    >>> to_wsl_path(r"C:\\Users\\me\\itf")
    '/mnt/c/Users/me/itf'
    >>> to_wsl_path("/home/me/itf")
    '/home/me/itf'
    """
    text = str(path)
    m = _DRIVE_RE.match(text)
    if not m:
        return text.replace("\\", "/")
    drive, rest = m.groups()
    rest = rest.replace("\\", "/")
    return f"/mnt/{drive.lower()}/{rest}".rstrip("/") or f"/mnt/{drive.lower()}/"


def from_wsl_path(path: str) -> str:
    """Inverse of :func:`to_wsl_path` for ``/mnt/<drive>/...`` paths."""
    parts = path.split("/")
    if len(parts) >= 3 and parts[0] == "" and parts[1] == "mnt" and len(parts[2]) == 1:
        rest = "/".join(parts[3:])
        return str(PureWindowsPath(f"{parts[2].upper()}:\\") / rest.replace("/", "\\"))
    return path


def shq(text: str) -> str:
    """POSIX single-quote a string for embedding in a ``bash -c`` script.

    Use for *data* -- paths that came from the filesystem. Nothing inside is expanded.
    """
    return "'" + text.replace("'", "'\\''") + "'"


def shq_expand(text: str) -> str:
    """Double-quote a string, leaving ``$VAR`` expansion intact.

    Use for *configuration* -- the ``fo`` path and config directory are written as
    ``$HOME/bin/fo`` so the Linux user's home directory never has to be discovered from
    the Windows side. Single-quoting those would pass the literal string ``$HOME`` to the
    kernel, which fails silently: ``fo`` never runs, no output files appear, and every
    designation comes back as "not returned".
    """
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`")
    return f'"{escaped}"'


@dataclass(frozen=True, slots=True)
class Shell:
    """How to run a POSIX command line: through ``wsl.exe`` on Windows, directly elsewhere.

    ``fo_path`` and ``config_dir`` are *WSL-side* strings and may contain ``$HOME``; they
    are expanded by the shell, not by Python, so the caller never has to know the Linux
    user's home directory.
    """

    fo_path: str = DEFAULT_FO
    config_dir: str = DEFAULT_CONFIG_DIR
    use_wsl: bool | None = None  # None -> decide from the platform

    @property
    def via_wsl(self) -> bool:
        return on_windows() if self.use_wsl is None else self.use_wsl

    def argv(self, script: str) -> list[str]:
        if self.via_wsl:
            return ["wsl.exe", "-e", "bash", "-c", script]
        return ["bash", "-c", script]

    def run(
        self,
        script: str,
        *,
        timeout: float | None = 900.0,
        check: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        """Run ``script`` under the POSIX shell. stdin is closed so ``fo`` never blocks."""
        argv = self.argv(script)
        if self.via_wsl and shutil.which("wsl.exe") is None:
            raise WslError("wsl.exe not found on PATH; cannot reach the Find_Orb build")
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdin=subprocess.DEVNULL,
                timeout=timeout,
                # `fo` exits non-zero in situations that still produce complete output
                # (e.g. after excluding daylight observations), so the return code is
                # recorded and reported, never used to decide whether to parse.
                check=False,
            )
        except FileNotFoundError as exc:  # pragma: no cover - platform-dependent
            raise WslError(f"could not launch {argv[0]}: {exc}") from exc
        if check and proc.returncode != 0:
            raise WslError(f"command failed ({proc.returncode}): {proc.stderr[-2000:]}")
        return proc

    def path(self, p: str | os.PathLike[str]) -> str:
        """Translate a host path for use inside the shell, making it absolute first.

        The absolute step is not a nicety. A *relative* Windows path has no drive letter,
        so :func:`to_wsl_path` passes it through unchanged and it is then resolved against
        whatever the shell's working directory happens to be. ``fo`` is invoked as
        ``cd <workdir> && fo obs.txt -O <workdir>``, so a relative ``data/fits/chunk0000``
        becomes ``data/fits/chunk0000/data/fits/chunk0000`` for ``-O`` -- and ``fo`` exits
        **0**, prints nothing, and writes its results somewhere nobody reads. The CLI's
        own default (``--workdir data/fits``) is relative, so this was the difference
        between 916 designations converging and 0.
        """
        if not self.via_wsl:
            return str(p)
        text = str(p)
        if not _DRIVE_RE.match(text) and not text.startswith("/"):
            text = str(Path(text).resolve())
        return to_wsl_path(text)

    def version(self) -> dict[str, str]:
        """Probe the installed Find_Orb: binary path, mtime, and its self-reported version.

        ``fo`` with no arguments prints a usage line and exits 0, which is enough to prove
        the binary exists and links. The version string is compiled in and appears in every
        ``elements.txt``, so we read it from the config directory's copy if one exists and
        otherwise report the binary's mtime.
        """
        script = (
            f"FO={self.fo_path}; CFG={self.config_dir}; "
            'printf "fo_path=%s\\n" "$FO"; '
            'if [ -x "$FO" ]; then printf "fo_exists=yes\\n"; '
            'printf "fo_mtime=%s\\n" "$(date -u -r "$FO" +%Y-%m-%dT%H:%M:%SZ)"; '
            'printf "fo_usage=%s\\n" "$("$FO" 2>&1 | head -1)"; '
            'else printf "fo_exists=no\\n"; fi; '
            'if [ -d "$CFG" ]; then printf "config_files=%s\\n" "$(ls "$CFG" | wc -l)"; '
            'printf "jpl_de=%s\\n" '
            '"$(ls "$CFG" | grep -E \'^(linux_|lnx|unix\\.|jpleph|sub_de|inpop)\' | tr \'\\n\' \' \')"; '
            'else printf "config_files=0\\n"; fi'
        )
        proc = self.run(script, timeout=60)
        out: dict[str, str] = {}
        for line in proc.stdout.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                out[k.strip()] = v.strip()
        return out

    def available(self) -> bool:
        try:
            return self.version().get("fo_exists") == "yes"
        except WslError:
            return False


def default_shell() -> Shell:
    """Build a :class:`Shell` from the environment, falling back to the documented layout."""
    return Shell(
        fo_path=os.environ.get(ENV_FO, DEFAULT_FO),
        config_dir=os.environ.get(ENV_CONFIG, DEFAULT_CONFIG_DIR),
    )


def ensure_host_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
