"""Small filesystem primitives. Nothing here executes imported skill code."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from datetime import datetime, timezone


class LoomError(ValueError):
    """A failed precondition; the caller should not bypass it automatically."""


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def object_digest(obj):
    return digest(canonical(obj))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def atomic_write(path, data, mode=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".skillloom-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_json(path, obj):
    atomic_write(path, json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")


def valid_name(name):
    return isinstance(name, str) and len(name) <= 64 and bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name))


def relative_path(value):
    """Reject traversal, Windows drives/ADS, and ambiguous portable filenames."""
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise LoomError("Expected a portable relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in {"", ".", ".."} for p in value.split("/")):
        raise LoomError("Absolute and traversal paths are forbidden")
    for part in path.parts:
        if part.endswith((".", " ")) or re.match(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", part, re.I):
            raise LoomError("Nonportable filename")
    return path


def is_link(path):
    path = Path(path)
    try:
        mode = path.lstat()
    except FileNotFoundError:
        return False
    return path.is_symlink() or bool(getattr(mode, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def contained(child, parent):
    try:
        Path(child).resolve().relative_to(Path(parent).resolve())
        return True
    except ValueError:
        return False


def snapshot(folder):
    """Exact file hashes, rejecting all links, devices, and embedded repositories."""
    folder = Path(folder)
    if is_link(folder):
        raise LoomError("Mutation targets cannot be links; select the reviewed physical skills root")
    if not folder.exists():
        return {}
    if not folder.is_dir():
        raise LoomError("Expected a skill directory")
    result = {}
    for parent, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs + files:
            path = Path(parent) / name
            if is_link(path):
                raise LoomError(f"Nested link refused: {name}")
            if name in {".git", ".svn"}:
                raise LoomError("Embedded source-control metadata is not a runtime skill")
        for name in files:
            path = Path(parent) / name
            if not path.is_file():
                raise LoomError("Special files are not supported")
            relative = path.relative_to(folder).as_posix()
            relative_path(relative)
            result[relative] = digest(path.read_bytes())
    return dict(sorted(result.items()))


def file_modes(folder, hashes):
    modes = {}
    for relative in hashes:
        mode = stat.S_IMODE((Path(folder) / relative).stat().st_mode)
        if mode & 0o7000:
            raise LoomError("Special permission bits are not supported for skills")
        modes[relative] = mode
    return modes


def prune_empty(folder, stop):
    """Remove empty directories only; never perform recursive deletion."""
    folder, stop = Path(folder), Path(stop)
    while folder != stop and contained(folder, stop):
        try:
            folder.rmdir()
        except OSError:
            return
        folder = folder.parent
