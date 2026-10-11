#!/usr/bin/env python3
"""Restore a historical snapshot through a new, fast-forward-only commit."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import uuid


def git(repo: Path, *arguments: str, input_text: str | None = None,
        environment: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *arguments], input=input_text,
        text=True, capture_output=True, env=environment,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Git command failed")
    return result.stdout.strip()


def restore_version(repo: Path, version: str, scanner: Path,
                    remote: str = "origin", branch: str = "main") -> dict[str, str]:
    """Validate a trusted historical tree and atomically publish its new commit.

    The scanner comes from the permanent control branch, never from the selected
    historical snapshot. Neither the checkout nor any local branch is changed.
    A competing remote update makes the atomic push fail without publishing the
    backup tag or overwriting that update.
    """
    if not version or version.startswith("-") or any(c in version for c in "\r\n\0"):
        raise ValueError("Specify a commit SHA or tag")
    git(repo, "check-ref-format", f"refs/heads/{branch}")
    git(repo, "fetch", "--no-tags", remote,
        f"+refs/heads/{branch}:refs/remotes/{remote}/{branch}")
    git(repo, "fetch", "--tags", remote)
    previous = git(repo, "rev-parse", "--verify", f"refs/remotes/{remote}/{branch}^{{commit}}")
    # Only full hexadecimal commit IDs and exact tag names are accepted. Git
    # revision expressions (HEAD~, ranges, reflogs) are deliberately unsupported.
    is_sha = len(version) == 40 and all(c in "0123456789abcdefABCDEF" for c in version)
    if is_sha:
        target_ref = version
    else:
        git(repo, "check-ref-format", f"refs/tags/{version}")
        target_ref = f"refs/tags/{version}"
    target = git(repo, "rev-parse", "--verify", "--end-of-options", f"{target_ref}^{{commit}}")
    git(repo, "merge-base", "--is-ancestor", target, previous)
    check = subprocess.run(
        [sys.executable, str(scanner.resolve()), "--tree", target],
        cwd=repo, text=True, capture_output=True,
    )
    if check.returncode:
        raise RuntimeError("Snapshot security check failed: " + (check.stderr or check.stdout).strip())
    tree = git(repo, "rev-parse", f"{target}^{{tree}}")
    environment = os.environ.copy()
    environment.update({
        "GIT_AUTHOR_NAME": "RDV", "GIT_AUTHOR_EMAIL": "dotianryndin@gmail.com",
        "GIT_COMMITTER_NAME": "RDV", "GIT_COMMITTER_EMAIL": "dotianryndin@gmail.com",
    })
    restored = git(repo, "commit-tree", tree, "-p", previous,
                   input_text=f"Restore snapshot {target}\n", environment=environment)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_tag = f"before-restore/{timestamp}-{previous[:12]}-{uuid.uuid4().hex[:12]}"
    git(repo, "push", "--atomic", remote,
        f"{previous}:refs/tags/{backup_tag}", f"{restored}:refs/heads/{branch}")
    remote_tip = git(repo, "ls-remote", remote, f"refs/heads/{branch}").split()[0]
    if remote_tip != restored:
        raise RuntimeError("Restore was pushed, but the remote branch has changed again; inspect history")
    return {"previous": previous, "target": target, "tree": tree,
            "commit": restored, "backup_tag": backup_tag}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Full commit SHA or exact tag name")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="main")
    arguments = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    try:
        result = restore_version(repo, arguments.version,
                                 repo / "scripts/check_repository.py",
                                 arguments.remote, arguments.branch)
    except (RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
    lines = ["Восстановление завершено."] + [f"{key}: {value}" for key, value in result.items()]
    print("\n".join(lines))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as output:
            output.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
