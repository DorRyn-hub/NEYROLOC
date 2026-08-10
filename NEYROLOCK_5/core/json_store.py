"""Small, dependency-free helpers for durable local JSON files.

The application keeps configuration, chat history and model metadata in JSON.
Writing those files in-place can leave a truncated document when the process is
interrupted.  These helpers serialise first and replace the destination only
after the temporary file has been flushed to disk.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

try:  # POSIX stdlib; Windows keeps the documented in-process fallback.
    import fcntl
except ImportError:  # pragma: no cover - exercised on non-POSIX platforms
    fcntl = None  # type: ignore[assignment]


DEFAULT_MAX_JSON_BYTES = 16 * 1024 * 1024


class JsonStoreError(ValueError):
    """A local JSON document is unreadable or has an unexpected shape."""


def ensure_private_directory(path: Path) -> None:
    """Create *path* and make it private where POSIX permissions are available."""
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        # Windows and some network filesystems do not implement POSIX modes.
        pass


class _AdvisoryFileLock:
    """Context manager kept explicit for Python 3.14 standalone builds.

    Nuitka 4.0 cannot currently compile ``contextlib.contextmanager`` wrappers
    with Python 3.14's deferred annotations reliably.  A small conventional
    context manager has identical behaviour and avoids that runtime-only
    packaging failure.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._handle: Any | None = None
        self._locked = False

    def __enter__(self) -> bool:
        ensure_private_directory(self._path.parent)
        self._handle = self._path.open("a+b")
        try:
            self._path.chmod(0o600)
        except OSError:
            pass
        if fcntl is None:
            return False
        try:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX)
        except BaseException:
            self._handle.close()
            self._handle = None
            raise
        self._locked = True
        return True

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        handle = self._handle
        self._handle = None
        if handle is None:
            return
        try:
            if self._locked and fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._locked = False
            handle.close()


def advisory_file_lock(path: Path) -> _AdvisoryFileLock:
    """Hold an interprocess advisory lock when the platform supports ``flock``.

    The yielded flag is ``False`` on platforms without ``fcntl`` so callers can
    retain their in-process lock and document the remaining cross-process risk.
    """
    return _AdvisoryFileLock(path)


def read_json_object(
    path: Path,
    *,
    max_bytes: int = DEFAULT_MAX_JSON_BYTES,
) -> dict[str, Any]:
    """Read a size-bounded JSON object.

    A root list/scalar is rejected so callers never fail later with obscure
    ``.get``/``.items`` errors.
    """
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")

    try:
        with path.open("rb") as handle:
            raw = handle.read(max_bytes + 1)
    except OSError:
        raise

    if len(raw) > max_bytes:
        raise JsonStoreError(
            f"JSON-файл слишком большой (максимум {max_bytes} байт): {path}"
        )
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise JsonStoreError(f"Некорректный JSON-файл: {path}") from exc
    if not isinstance(data, dict):
        raise JsonStoreError(f"Корнем JSON должен быть объект: {path}")
    return data


def atomic_write_text(path: Path, text: str, *, mode: int = 0o600) -> None:
    """Atomically replace *path* with UTF-8 *text* and fsync the result."""
    ensure_private_directory(path.parent)
    fd, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        fchmod = getattr(os, "fchmod", None)
        try:
            if callable(fchmod):
                fchmod(fd, mode)
        except OSError:
            pass
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            path.chmod(mode)
        except OSError:
            pass

        # Persist the directory entry as well on filesystems that support it.
        directory_fd: int | None = None
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
            os.fsync(directory_fd)
        except OSError:
            pass
        finally:
            if directory_fd is not None:
                os.close(directory_fd)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


def atomic_write_json(
    path: Path,
    data: dict[str, Any],
    *,
    mode: int = 0o600,
    max_bytes: int | None = None,
) -> None:
    """Serialise a JSON object and replace *path* atomically."""
    if not isinstance(data, dict):
        raise TypeError("data must be a dictionary")
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if max_bytes is not None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        size = len(text.encode("utf-8"))
        if size > max_bytes:
            raise JsonStoreError(
                f"JSON-файл слишком большой (максимум {max_bytes} байт): {path}"
            )
    atomic_write_text(path, text, mode=mode)
