import json

import pytest
from mcp import Client

from eufylife_mcp import server
from eufylife_mcp.service import ScaleService
from tests.factories import ANN, ANN_SMITH, BOB
from tests.fakes import NOW, FakeEufyClient

TOOLS = {"list_members", "get_latest_measurement", "get_measurement_history"}


@pytest.fixture
def fake_client():
    client = FakeEufyClient([ANN, BOB])
    server.set_service(ScaleService(client, clock=lambda: NOW))
    yield client
    server.set_service(None)


async def call(name, arguments=None):
    async with Client(server.mcp) as client:
        return await client.call_tool(name, arguments or {})


async def test_lists_three_read_only_tools(fake_client):
    async with Client(server.mcp) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
    assert set(tools) == TOOLS
    assert all(t.annotations.read_only_hint for t in tools.values())
    assert tools["list_members"].input_schema.get("properties", {}) == {}
    for name in TOOLS - {"list_members"}:
        schema = tools[name].input_schema
        assert schema.get("required", []) == []
        assert "list_members" in schema["properties"]["member"]["description"]
    days = tools["get_measurement_history"].input_schema["properties"]["days"]
    assert (days["default"], days["minimum"], days["maximum"]) == (30, 1, 3650)


async def test_list_members(fake_client):
    result = await call("list_members")
    assert not result.is_error
    members = result.structured_content["members"]
    assert [(m["name"], m["is_default"]) for m in members] == [("Ann Lee", True), ("Bob", False)]


async def test_get_latest_measurement(fake_client):
    result = await call("get_latest_measurement", {"member": "bob"})
    assert not result.is_error
    body = result.structured_content
    assert body["member"]["name"] == "Bob"
    assert body["measurement"]["weight_kg"] == 81.5
    assert "age_hours" in body["measurement"]
    assert json.loads(result.content[0].text) == body


async def test_get_measurement_history_sorted(fake_client):
    result = await call("get_measurement_history", {"member": "cust-ann", "days": 30})
    body = result.structured_content
    assert (body["count"], body["days"]) == (2, 30)
    assert [m["weight_kg"] for m in body["measurements"]] == [65.8, 65.2]


async def test_history_days_out_of_range_is_rejected(fake_client):
    result = await call("get_measurement_history", {"days": 0})
    assert result.is_error


async def test_tool_error_is_reported_not_raised():
    server.set_service(ScaleService(FakeEufyClient([BOB, ANN_SMITH])))
    try:
        result = await call("get_latest_measurement")  # no default member, none chosen
    finally:
        server.set_service(None)
    assert result.is_error
    assert "several members" in result.content[0].text
    assert "Ann Smith" in result.content[0].text


async def test_main_exits_on_missing_credentials(monkeypatch, capsys):
    monkeypatch.delenv("EUFYLIFE_EMAIL", raising=False)
    monkeypatch.delenv("EUFYLIFE_PASSWORD", raising=False)
    with pytest.raises(SystemExit) as info:
        server.main()
    assert info.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "EUFYLIFE_EMAIL" in captured.err


def test_build_client_uses_settings():
    from eufylife_mcp.config import load_settings
    from eufylife_mcp.core.client import EufyLifeClient

    settings = load_settings(
        {
            "EUFYLIFE_EMAIL": "me@example.com",
            "EUFYLIFE_PASSWORD": " pass word ",
            "EUFYLIFE_COUNTRY": "gb",
        }
    )
    client = server.build_client(settings)
    assert isinstance(client, EufyLifeClient)
    assert client.country == "GB"
