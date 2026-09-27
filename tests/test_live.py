"""Hits the real EufyLife API. Run with: uv run pytest -m live"""

import os

import pytest
from mcp import Client

from eufylife_mcp import server
from eufylife_mcp.config import load_settings
from eufylife_mcp.service import ScaleService

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not (os.environ.get("EUFYLIFE_EMAIL") and os.environ.get("EUFYLIFE_PASSWORD")),
        reason="needs EUFYLIFE_EMAIL and EUFYLIFE_PASSWORD",
    ),
]


async def test_live_list_members_and_history():
    settings = load_settings()
    server.set_service(ScaleService(server.build_client(settings)))
    try:
        async with Client(server.mcp) as mcp_client:
            members = await mcp_client.call_tool("list_members", {})
            assert not members.is_error, members.content
            first = members.structured_content["members"][0]["member_id"]
            history = await mcp_client.call_tool(
                "get_measurement_history", {"member": first, "days": 3650}
            )
            assert not history.is_error, history.content
            for measurement in history.structured_content["measurements"]:
                assert measurement.get("weight_kg", 1) > 0
    finally:
        server.set_service(None)
