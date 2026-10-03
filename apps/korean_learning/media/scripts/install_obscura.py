#!/usr/bin/env python3
"""Install the pinned upstream Linux x86_64 Obscura release locally."""
import hashlib
from pathlib import Path
import platform
import tarfile
import urllib.request

VERSION = 'v0.2.3'
SHA256 = '1534d1e6ddaf3d080ec4091eb41d0a4d8cc042a48b607d3c410fc13b482a9eec'
URL = f'https://github.com/h4ckf0r0day/obscura/releases/download/{VERSION}/obscura-x86_64-linux.tar.gz'
if platform.system() != 'Linux' or platform.machine() != 'x86_64':
    raise SystemExit('This installer targets Linux x86_64. Set OBSCURA_BINARY to a matching upstream binary on other platforms.')
destination = Path(__file__).resolve().parents[1] / '.tools/obscura'
destination.mkdir(parents=True, exist_ok=True)
archive = destination / 'release.tar.gz'
if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
    with urllib.request.urlopen(URL, timeout=60) as response:
        archive.write_bytes(response.read())
if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
    raise SystemExit('Release checksum mismatch')
with tarfile.open(archive) as source:
    source.extractall(destination, filter='data')
print(f'Installed Obscura {VERSION}: {destination / "obscura"}')
