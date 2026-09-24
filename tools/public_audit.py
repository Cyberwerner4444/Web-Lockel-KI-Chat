#!/usr/bin/env python3
"""Fail closed when a public checkout contains obvious private material."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".css",
    ".example",
    ".html",
    ".js",
    ".md",
    ".py",
    ".txt",
    ".json",
    ".service",
    ".toml",
    ".yaml",
    ".yml",
}
TEXT_FILENAMES = {".env", ".env.example", ".gitignore", "Caddyfile"}
FORBIDDEN_TEXT = (
    re.compile(r"\b[a-z0-9._%+-]+@(?!example\.com\b)[a-z0-9.-]+\.[a-z]{2,}\b", re.I),
    re.compile(r"\b[a-z0-9-]+\.ch\b|\b[a-z0-9-]+\.mail\b", re.I),
    re.compile(r"(?<!127\.0\.0\.1)\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    re.compile(r"telegram|nextcloud|referral" + r"code|public" + r"[-.]pool\.io", re.I),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|(?<![A-Za-z0-9])sk-[A-Za-z0-9]{8,})"),
    re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"),
)
FORBIDDEN_SUFFIXES = {
    ".db",
    ".gguf",
    ".key",
    ".model",
    ".onnx",
    ".pem",
    ".pth",
    ".pt",
    ".safetensors",
    ".secret",
    ".sqlite",
    ".sqlite3",
    ".sqlite3-shm",
    ".sqlite3-wal",
    ".stl",
    ".zip",
}
LEGACY_CHAT_EXCLUSIONS = {
    "index.html",
    "support.html",
    "live-mining.html",
    "live-mining.js",
    "live-mining-worker.js",
    "logos.html",
    "rechtliches.html",
}
MAX_PUBLIC_FILE_BYTES = 50 * 1024 * 1024


def public_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and ".venv" not in path.parts
        and "__pycache__" not in path.parts
        and not path.name.endswith(".pyc")
    ]


def main() -> int:
    violations: list[str] = []
    for path in public_files():
        relative = path.relative_to(ROOT)
        if relative == Path("tools/public_audit.py"):
            continue
        if path.name == ".env" or (
            path.name.startswith(".env.") and path.name != ".env.example"
        ):
            violations.append(f"private environment file: {relative}")
        if path.name in LEGACY_CHAT_EXCLUSIONS:
            violations.append(f"out-of-scope legacy page/feature: {relative}")
        if "web-upload" in relative.parts or "helmut-logo" in path.name.lower():
            violations.append(f"out-of-scope upload/logo asset: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            violations.append(f"forbidden file type: {relative}")
        if path.stat().st_size > MAX_PUBLIC_FILE_BYTES:
            violations.append(f"file exceeds public size limit: {relative}")
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_FILENAMES:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                violations.append(f"non-UTF-8 text file: {relative}")
                continue
            scan_text = text.replace("127.0.0.1", "")
            for pattern in FORBIDDEN_TEXT:
                if pattern.search(scan_text):
                    violations.append(f"private/production pattern {pattern.pattern!r}: {relative}")

    git_config = ROOT / ".git" / "config"
    if git_config.exists():
        config_text = git_config.read_text(encoding="utf-8", errors="replace")
        remotes = re.findall(r"^\s*url\s*=\s*(\S+)", config_text, re.M)
        if any("github.com" not in remote and "example.com" not in remote for remote in remotes):
            violations.append("non-public remote found in .git/config")
        try:
            author_output = subprocess.check_output(
                ["git", "-C", str(ROOT), "log", "--format=%an <%ae>"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            identities = [line for line in author_output.splitlines() if line.strip()]
            if any(
                "users.noreply.github.com" not in identity
                and "example.com" not in identity
                for identity in identities
            ):
                violations.append("non-anonymous author identity found in Git history")
        except (OSError, subprocess.CalledProcessError):
            pass

    if violations:
        print("PUBLIC AUDIT FAILED")
        print("\n".join(f"- {violation}" for violation in sorted(set(violations))))
        return 1
    print(f"PUBLIC AUDIT PASSED ({len(public_files())} files checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
