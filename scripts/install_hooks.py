#!/usr/bin/env python3
"""Install local Git guards without replacing an existing hook directory."""
from pathlib import Path
import shutil
import subprocess


def main():
    root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).decode().strip())
    source = Path(__file__).resolve().parent.parent
    git_dir = Path(subprocess.check_output(['git', 'rev-parse', '--absolute-git-dir']).decode().strip())
    persistent_hooks = git_dir / 'project-hooks'
    guards = git_dir / 'project-guards'
    if not shutil.which('gitleaks'):
        raise SystemExit('Install gitleaks first (macOS: brew install gitleaks)')
    current = subprocess.run(['git', 'config', '--get', 'core.hooksPath'], capture_output=True, text=True).stdout.strip()
    if current and current not in {'.githooks', str(persistent_hooks)}:
        raise SystemExit('Existing custom hooks detected; integrate guards manually')
    guards.mkdir(exist_ok=True)
    persistent_hooks.mkdir(exist_ok=True)
    for name in ['check_repository.py', 'pre_push.py']:
        shutil.copy2(source / 'scripts' / name, guards / name)
    shutil.copy2(source / '.gitleaks.toml', guards / 'gitleaks.toml')
    hooks = {
        'pre-commit': 'python3 "$guards/check_repository.py" --index',
        'commit-msg': 'python3 "$guards/check_repository.py" --message-file "$1"',
        'pre-push': 'python3 "$guards/pre_push.py" "$@"',
    }
    for name, command in hooks.items():
        path = root / '.githooks' / name
        path.parent.mkdir(exist_ok=True)
        content = '#!/bin/sh\nset -eu\nguards="$(git rev-parse --git-path project-guards)"\n' + command + '\n'
        path.write_text(content)
        path.chmod(0o755)
        persistent = persistent_hooks / name
        persistent.write_text(content)
        persistent.chmod(0o755)
    for key, value in [('core.hooksPath', str(persistent_hooks)), ('pull.ff', 'only'),
                       ('fetch.fsckObjects', 'true'), ('transfer.fsckObjects', 'true'),
                       ('push.default', 'simple')]:
        subprocess.run(['git', 'config', '--local', key, value], check=True)
    print('Local commit/push guards installed')


if __name__ == '__main__':
    main()
