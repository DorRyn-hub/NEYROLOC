#!/usr/bin/env python3
"""Install a pinned scanner after SHA-256 verification (Linux Actions runner)."""
import hashlib
import io
import os
import pathlib
import tarfile
import urllib.request

VERSION = "8.30.1"
BASE = f"https://github.com/gitleaks/gitleaks/releases/download/v{VERSION}/"
NAME = f"gitleaks_{VERSION}_linux_x64.tar.gz"


def main():
    checksums = urllib.request.urlopen(BASE + f"gitleaks_{VERSION}_checksums.txt").read().decode()
    expected = next(line.split()[0] for line in checksums.splitlines() if line.split()[-1] == NAME)
    data = urllib.request.urlopen(BASE + NAME).read()
    if hashlib.sha256(data).hexdigest() != expected:
        raise SystemExit("Scanner checksum mismatch")
    target = pathlib.Path.home() / ".local/bin/gitleaks"
    target.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        member = archive.getmember("gitleaks")
        if not member.isfile():
            raise SystemExit("Unexpected scanner archive")
        target.write_bytes(archive.extractfile(member).read())
    target.chmod(0o755)
    if os.environ.get("GITHUB_PATH"):
        with open(os.environ["GITHUB_PATH"], "a") as output:
            output.write(str(target.parent) + "\n")
    print("Verified scanner installed")


if __name__ == "__main__":
    main()
