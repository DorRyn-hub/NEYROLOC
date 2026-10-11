#!/usr/bin/env python3
"""Reject branch rewrites, tag replacement, unsafe snapshots and metadata."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_repository import check, git, metadata

ZERO = '0' * 40


def main():
    for line in sys.stdin:
        local_ref, local_oid, remote_ref, remote_oid = line.split()
        metadata(local_ref.encode())
        metadata(remote_ref.encode())
        if local_oid == ZERO:
            raise ValueError('Deleting remote branches/tags is blocked')
        if remote_ref.startswith('refs/tags/') and remote_oid != ZERO and local_oid != remote_oid:
            raise ValueError('Published tags are immutable')
        if remote_ref.startswith('refs/heads/') and remote_oid != ZERO:
            if subprocess.run(['git', 'merge-base', '--is-ancestor', remote_oid, local_oid]).returncode:
                raise ValueError('History overwrite blocked; fetch and integrate remote history')
        if local_oid == remote_oid:
            continue
        if remote_ref.startswith('refs/tags/'):
            metadata(git('cat-file', '-p', local_oid))
        commit = git('rev-parse', local_oid + '^{commit}').decode().strip()
        check(commit)
        # Old remote history is retained; every newly published commit is inspected.
        revs = git('rev-list', commit, '--not', '--remotes=origin').decode().splitlines()
        for revision in revs:
            metadata(git('show', '-s', '--format=%B%n%an%n%ae%n%cn%n%ce', revision))
            if revision != commit:
                check(revision)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
