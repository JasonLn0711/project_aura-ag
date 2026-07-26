#!/usr/bin/env python3
"""Reject sensitive partner and person labels in publishable repository files."""

from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path


PERSON_LABEL = b"M" + b"ax"
PARTNER_LABEL = b"vo" + b"iss"
PERSON_PATTERN = re.compile(
    rb"(?<![A-Za-z])" + re.escape(PERSON_LABEL) + rb"(?![A-Za-z])"
)
PARTNER_PATTERN = re.compile(re.escape(PARTNER_LABEL), re.IGNORECASE)


def _tracked_and_untracked_files(root: Path) -> tuple[Path, ...]:
    output = subprocess.check_output(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        cwd=root,
    )
    return tuple(root / name.decode() for name in output.split(b"\0") if name)


def _labels(data: bytes) -> tuple[str, ...]:
    labels = []
    if PERSON_PATTERN.search(data):
        labels.append("person label")
    if PARTNER_PATTERN.search(data):
        labels.append("partner label")
    return tuple(labels)


def scan_repository(root: Path) -> list[str]:
    findings: list[str] = []
    for path in _tracked_and_untracked_files(root):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        for label in _labels(relative.as_posix().encode()):
            findings.append(f"{relative}: filename contains {label}")
        data = path.read_bytes()
        for label in _labels(data):
            findings.append(f"{relative}: content contains {label}")
        if path.suffix.lower() != ".zip":
            continue
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                member_name = member.filename.encode()
                for label in _labels(member_name):
                    findings.append(
                        f"{relative}!{member.filename}: filename contains {label}"
                    )
                for label in _labels(archive.read(member)):
                    findings.append(
                        f"{relative}!{member.filename}: content contains {label}"
                    )
    return findings


def registered_worktrees(root: Path) -> tuple[Path, ...]:
    output = subprocess.check_output(
        ["git", "worktree", "list", "--porcelain"],
        cwd=root,
        text=True,
    )
    return tuple(
        Path(line.removeprefix("worktree "))
        for line in output.splitlines()
        if line.startswith("worktree ")
    )


def scan_registered_worktrees(root: Path) -> list[str]:
    findings: list[str] = []
    for worktree in registered_worktrees(root):
        findings.extend(
            f"{worktree}: {finding}" for finding in scan_repository(worktree)
        )
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    args = sys.argv[1:]
    if args not in ([], ["--all-worktrees"]):
        print(
            "usage: check_public_anonymization.py [--all-worktrees]",
            file=sys.stderr,
        )
        return 2
    findings = (
        scan_registered_worktrees(root)
        if args
        else scan_repository(root)
    )
    if findings:
        print("\n".join(findings))
        return 1
    scope = (
        f"{len(registered_worktrees(root))} registered worktrees"
        if args
        else "the current checkout"
    )
    print(f"Public anonymization check passed for {scope}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
