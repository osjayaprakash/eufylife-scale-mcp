"""The server must run on its own EufyLife client: no requests, no aiohttp."""

import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
FORBIDDEN = re.compile(r"^\s*(?:import|from)\s+(requests|aiohttp)\b", re.MULTILINE)


def test_src_does_not_import_requests_or_aiohttp():
    offenders = [
        f"{path.relative_to(SRC)}: {match.group(1)}"
        for path in sorted(SRC.rglob("*.py"))
        for match in FORBIDDEN.finditer(path.read_text())
    ]
    assert offenders == []
