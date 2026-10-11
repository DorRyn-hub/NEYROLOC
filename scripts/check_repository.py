#!/usr/bin/env python3
"""Inspect the complete staged/selected Git snapshot without printing secrets."""
import argparse
import fnmatch
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile

FORBIDDEN = bytes([99, 111, 100, 101, 120])
PRIVATE_DIRS = {'.git', '.venv', 'venv', 'env', '.idea', '.vscode', '__pycache__',
                '.ruff_cache', '.pytest_cache', '.mypy_cache', 'dist', 'deployment',
                'build', 'output', 'backup', 'backups', 'xcuserdata', 'DerivedData',
                'chats', 'sessions', 'logs', 'runtime', 'user_data'}
PRIVATE_NAMES = {'chat.json', 'history.json', 'config.json', 'registry.json',
                 'frpc.toml', 'frps.toml', 'token', 'tokens.json', '.DS_Store',
                 'CLAUDE.local.md', 'MORNING_BRIEF.md'}
PRIVATE_GLOBS = ('*.pem', '*.key', '*.p12', '*.pfx', '*.keystore', '*.mobileprovision',
                 '*.db', '*.db-*', '*.sqlite*', '*.log', '*.pyc', '*.apk', '*.ipa',
                 '*.idsig', '*.zip', '*.dmg', '*.tar*', '*.tgz', '*.7z', '*.bak',
                 '*.backup', '*.gguf', '*.safetensors', '*.xcuserstate', 'id_rsa*',
                 'id_ed25519*', 'credentials*', 'secrets*', 'cookies*', '*.app', '*.build')


def git(*args):
    return subprocess.check_output(['git', *args])


def private_path(path):
    p = PurePosixPath(path)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        return True
    if any(part in PRIVATE_DIRS for part in p.parts) or p.name in PRIVATE_NAMES:
        return True
    if p.name.startswith('.env') and p.name not in {'.env.example', '.env.template'}:
        return True
    return (any(fnmatch.fnmatch(p.name, pattern) for pattern in PRIVATE_GLOBS)
            or path == 'remote/frpc' or p.name.startswith(('config.local.', 'settings.local.')))


def metadata(data):
    if FORBIDDEN in data.lower():
        raise ValueError('Disallowed publication attribution')


def entries(tree=None):
    raw = git('ls-tree', '-rz', tree) if tree else git('ls-files', '--stage', '-z')
    for item in raw.split(b'\0'):
        if not item:
            continue
        head, path = item.split(b'\t', 1)
        fields = head.decode().split()
        mode, oid = fields[0], fields[2] if tree else fields[1]
        if not tree and fields[2] != '0':
            raise ValueError('Resolve index conflicts before committing')
        yield mode, oid, path.decode('utf-8')


def check(tree=None):
    scanner = shutil.which('gitleaks')
    if not scanner:
        raise ValueError('gitleaks is required; install it and run scripts/install_hooks.py')
    errors = []
    count = 0
    with tempfile.TemporaryDirectory(prefix='source-check-') as directory:
        root = Path(directory) / 'snapshot'
        root.mkdir()
        for mode, oid, path in entries(tree):
            count += 1
            if private_path(path):
                errors.append(f'{path}: private/artifact path')
                continue
            if mode not in {'100644', '100755'}:
                errors.append(f'{path}: symlink or embedded repository is not allowed')
                continue
            data = git('cat-file', 'blob', oid)
            if FORBIDDEN in path.lower().encode() or FORBIDDEN in data.lower():
                errors.append(f'{path}: disallowed publication attribution')
            # Personal local-machine paths are not portable documentation.
            if re.search(rb'/Users/[A-Za-z0-9_.-]+/', data):
                errors.append(f'{path}: personal absolute path')
            if len(data) > 10 * 1024 * 1024:
                errors.append(f'{path}: exceeds source-file size limit')
                continue
            destination = root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        report = Path(directory) / 'report.json'
        ignore = Path(directory) / 'empty-ignore'
        ignore.write_text('')
        result = subprocess.run([scanner, 'dir', str(root), '--redact=100', '--no-banner',
                                 '--config', str(Path(__file__).resolve().parents[1] / '.gitleaks.toml'),
                                 '--ignore-gitleaks-allow', '--gitleaks-ignore-path', str(ignore),
                                 '--report-format', 'json', '--report-path', str(report)],
                                capture_output=True)
        if result.returncode == 1:
            for item in json.loads(report.read_text()):
                name = os.path.relpath(item['File'], root)
                errors.append(f"{name}:{item['StartLine']}: secret pattern {item['RuleID']}")
        elif result.returncode != 0:
            errors.append('Secret scanner could not complete; publication blocked')
    if errors:
        raise ValueError('\n'.join(errors))
    print(f'Snapshot safety check passed: {count} files')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--tree')
    group.add_argument('--index', action='store_true')
    group.add_argument('--message-file')
    options = parser.parse_args()
    try:
        if options.message_file:
            metadata(Path(options.message_file).read_bytes())
            metadata(git('var', 'GIT_AUTHOR_IDENT'))
            metadata(git('var', 'GIT_COMMITTER_IDENT'))
        else:
            check(options.tree)
    except (ValueError, subprocess.CalledProcessError) as error:
        print(str(error))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
