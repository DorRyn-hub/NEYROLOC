#!/usr/bin/env python3
"""Install local Git guards without replacing an existing hook directory."""
from pathlib import Path
import shutil
import subprocess


def main():
    root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).decode().strip())
    if not shutil.which('gitleaks'):
        raise SystemExit('Install gitleaks first (macOS: brew install gitleaks)')
    current = subprocess.run(['git', 'config', '--get', 'core.hooksPath'], capture_output=True, text=True).stdout.strip()
    if current and current != '.githooks':
        raise SystemExit('Existing custom hooks detected; integrate guards manually')
    hooks = {
        'pre-commit': 'python3 scripts/check_repository.py --index',
        'commit-msg': 'python3 scripts/check_repository.py --message-file "$1"',
        'pre-push': 'python3 scripts/pre_push.py "$@"',
    }
    for name, command in hooks.items():
        path = root / '.githooks' / name
        path.parent.mkdir(exist_ok=True)
        path.write_text('#!/bin/sh\nset -eu\n' + command + '\n')
        path.chmod(0o755)
    for key, value in [('core.hooksPath', '.githooks'), ('pull.ff', 'only'),
                       ('fetch.fsckObjects', 'true'), ('transfer.fsckObjects', 'true'),
                       ('push.default', 'simple')]:
        subprocess.run(['git', 'config', '--local', key, value], check=True)
    print('Local commit/push guards installed')


if __name__ == '__main__':
    main()
