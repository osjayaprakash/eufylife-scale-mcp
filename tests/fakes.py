"""A scriptable stand-in for eufylife_mcp.core.client.EufyLifeClient."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from tests.factories import ANN, BOB, make_measurement

NOW = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


def default_records():
    return [
        make_measurement(ANN, datetime(2026, 9, 26, 7, 0, tzinfo=UTC), 65.2, record_id="a3"),
        make_measurement(ANN, datetime(2026, 9, 20, 7, 0, tzinfo=UTC), 65.8, record_id="a2"),
        make_measurement(ANN, datetime(2026, 6, 1, 7, 0, tzinfo=UTC), 68.0, record_id="a1"),
        make_measurement(BOB, datetime(2026, 9, 25, 8, 0, tzinfo=UTC), 81.5, record_id="b1"),
    ]


class FakeEufyClient:
    """Records calls; `fail_next[method]` holds exceptions to raise, one per call."""

    def __init__(self, members, records=None, *, auth_delay: float = 0.0):
        self.members = list(members)
        self.records = default_records() if records is None else list(records)
        self.auth_delay = auth_delay
        self.calls: list[tuple[str, datetime | None]] = []
        self.fail_next: dict[str, list[Exception]] = {}

    def _record(self, method: str, arg: datetime | None = None) -> None:
        self.calls.append((method, arg))
        queue = self.fail_next.get(method)
        if queue:
            raise queue.pop(0)

    def count(self, method: str) -> int:
        return sum(1 for name, _ in self.calls if name == method)

    async def authenticate(self) -> None:
        if self.auth_delay:
            await asyncio.sleep(self.auth_delay)
        self._record("authenticate")

    async def get_members(self):
        self._record("get_members")
        return list(self.members)

    async def measurements(self, after=None):
        # Like the real API, `after` narrows the result.
        self._record("measurements", after)
        return [r for r in self.records if after is None or r.time > after]
