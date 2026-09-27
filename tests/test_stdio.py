"""Run the real entry point as a subprocess: proves nothing but MCP frames reach stdout."""

import sys

from mcp import Client, StdioServerParameters

ENV = {
    "EUFYLIFE_EMAIL": "nobody@example.com",
    "EUFYLIFE_PASSWORD": "unused",
    "PATH": "",
}


async def test_stdio_server_starts_and_lists_tools():
    params = StdioServerParameters(command=sys.executable, args=["-m", "eufylife_mcp"], env=ENV)
    async with Client(params) as client:
        tools = await client.list_tools()
    assert {t.name for t in tools.tools} == {
        "list_members",
        "get_latest_measurement",
        "get_measurement_history",
    }
