"""MCP server exposing EufyLife smart scale measurements as read-only tools."""

from __future__ import annotations

import atexit
import logging
import sys
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from eufylife_mcp import formatting, tracing
from eufylife_mcp.config import ConfigError, Settings, load_settings
from eufylife_mcp.core.client import EufyLifeClient
from eufylife_mcp.service import ScaleService

mcp = MCPServer(
    "eufylife",
    instructions=(
        "Read-only access to weight and body composition measured by EufyLife smart scales. "
        "Weight is given in kg and lb; other metrics use the unit in their key "
        "(e.g. `body_fat_pct`, `muscle_mass_kg`). Metrics the scale did not measure are "
        "omitted. Timestamps are UTC."
    ),
)

_READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=True)

MemberArg = Annotated[
    str | None,
    Field(
        description=(
            "Name (e.g. 'Ann') or member_id from list_members. "
            "Omit for the account owner, or when the account has one member."
        )
    ),
]

DaysArg = Annotated[
    int,
    Field(ge=1, le=3650, description="How many days back to include, counting from now."),
]

_service: ScaleService | None = None


def set_service(service: ScaleService | None) -> None:
    global _service
    _service = service


def _get_service() -> ScaleService:
    if _service is None:
        raise RuntimeError("ScaleService is not configured; call main() or set_service().")
    return _service


@mcp.tool(annotations=_READ_ONLY)
@tracing.traced("list_members")
async def list_members() -> dict[str, Any]:
    """List the member profiles (people) on this EufyLife account."""
    members = await _get_service().list_members()
    return {"members": [formatting.member_to_dict(m) for m in members]}


@mcp.tool(annotations=_READ_ONLY)
@tracing.traced("get_latest_measurement")
async def get_latest_measurement(member: MemberArg = None) -> dict[str, Any]:
    """Most recent weigh-in with its body composition.

    Check `age_hours`: this is the last time the person stepped on the scale.
    """
    resolved, measurement = await _get_service().latest(member)
    return formatting.latest_response(resolved, measurement)


@mcp.tool(annotations=_READ_ONLY)
@tracing.traced("get_measurement_history")
async def get_measurement_history(member: MemberArg = None, days: DaysArg = 30) -> dict[str, Any]:
    """Weigh-ins from the last `days` days (default 30), oldest first."""
    resolved, measurements = await _get_service().history(member, days)
    return formatting.history_response(resolved, measurements, days=days)


def build_client(settings: Settings) -> EufyLifeClient:
    return EufyLifeClient(settings.email, settings.password, settings.country)


def main() -> None:
    # stdout carries the MCP protocol; every log line must go to stderr.
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"eufylife-scale-mcp: {exc}", file=sys.stderr)
        sys.exit(1)

    tracing.configure(settings)
    atexit.register(tracing.shutdown)
    set_service(ScaleService(build_client(settings)))
    mcp.run("stdio")
