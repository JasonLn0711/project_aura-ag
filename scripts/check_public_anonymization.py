#!/usr/bin/env python3
"""Reject sensitive partner and person labels across repository storage."""

from __future__ import annotations

import argparse
import io
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


def _display_path(path: Path) -> str:
    value = path.as_posix()
    return "<redacted-path>" if _labels(value.encode()) else value


def scan_repository(root: Path) -> list[str]:
    findings: list[str] = []
    for path in _tracked_and_untracked_files(root):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        display = _display_path(relative)
        for label in _labels(relative.as_posix().encode()):
            findings.append(f"{display}: filename contains {label}")
        data = path.read_bytes()
        for label in _labels(data):
            findings.append(f"{display}: content contains {label}")
        if path.suffix.lower() != ".zip":
            continue
        with zipfile.ZipFile(path) as archive:
            for index, member in enumerate(archive.infolist(), start=1):
                member_name = member.filename.encode()
                for label in _labels(member_name):
                    findings.append(
                        f"{display}!member-{index}: filename contains {label}"
                    )
                for label in _labels(archive.read(member)):
                    findings.append(
                        f"{display}!member-{index}: content contains {label}"
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


def _git_objects(root: Path) -> tuple[tuple[str, str], ...]:
    output = subprocess.check_output(
        [
            "git",
            "cat-file",
            "--batch-all-objects",
            "--batch-check=%(objectname) %(objecttype)",
        ],
        cwd=root,
        text=True,
    )
    return tuple(tuple(line.split()) for line in output.splitlines())


def scan_git_objects(root: Path) -> list[str]:
    findings: list[str] = []
    process = subprocess.Popen(
        ["git", "cat-file", "--batch"],
        cwd=root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    try:
        for object_id, expected_type in _git_objects(root):
            process.stdin.write(f"{object_id}\n".encode())
            process.stdin.flush()
            header = process.stdout.readline().decode().strip().split()
            if len(header) != 3 or header[1] != expected_type:
                raise RuntimeError(f"Unexpected git cat-file header for {object_id}")
            size = int(header[2])
            data = process.stdout.read(size)
            process.stdout.read(1)
            for label in _labels(data):
                findings.append(
                    f"object {object_id} ({expected_type}) contains {label}"
                )
            if expected_type != "blob" or not zipfile.is_zipfile(io.BytesIO(data)):
                continue
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                for index, member in enumerate(archive.infolist(), start=1):
                    for label in _labels(member.filename.encode()):
                        findings.append(
                            f"object {object_id} ZIP member {index} name contains {label}"
                        )
                    for label in _labels(archive.read(member)):
                        findings.append(
                            f"object {object_id} ZIP member {index} contains {label}"
                        )
    finally:
        process.stdin.close()
        process.stdout.close()
        process.wait()
    return findings


def _git_common_dir(root: Path) -> Path:
    value = subprocess.check_output(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=root,
        text=True,
    ).strip()
    path = Path(value)
    return path if path.is_absolute() else (root / path).resolve()


def scan_git_metadata(root: Path) -> list[str]:
    common_dir = _git_common_dir(root)
    findings: list[str] = []
    for path in common_dir.rglob("*"):
        relative = path.relative_to(common_dir)
        if not path.is_file() or relative.parts[:1] == ("objects",):
            continue
        display = _display_path(relative)
        for label in _labels(relative.as_posix().encode()):
            findings.append(f"git metadata {display}: filename contains {label}")
        for label in _labels(path.read_bytes()):
            findings.append(f"git metadata {display}: content contains {label}")
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-worktrees", action="store_true")
    parser.add_argument("--git-objects", action="store_true")
    parser.add_argument("--git-metadata", action="store_true")
    args = parser.parse_args()
    findings = (
        scan_registered_worktrees(root)
        if args.all_worktrees
        else scan_repository(root)
    )
    if args.git_objects:
        findings.extend(scan_git_objects(root))
    if args.git_metadata:
        findings.extend(scan_git_metadata(root))
    if findings:
        print("\n".join(findings))
        return 1
    scopes = [
        (
            f"{len(registered_worktrees(root))} registered worktrees"
            if args.all_worktrees
            else "the current checkout"
        )
    ]
    if args.git_objects:
        scopes.append("all local Git objects")
    if args.git_metadata:
        scopes.append("Git metadata")
    scope = ", ".join(scopes)
    print(f"Public anonymization check passed for {scope}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
