import json

import httpx2
import pytest

from eufylife_mcp.core import (
    APIError,
    AuthenticationError,
    LoginRejectedError,
    NetworkError,
    RateLimitError,
    ResponseShapeError,
)
from eufylife_mcp.core.client import APP_VERSION, CLIENT_ID, EufyLifeClient
from tests.core.mock_api import MockAPI, fixture

LOGIN = "home-api.eufylife.com/v1/user/v2/email/login/"


def make_client(api: MockAPI, *, password: str = "pw", country: str = "US", clock=None):
    kwargs = {} if clock is None else {"clock": clock}
    return EufyLifeClient("me@example.com", password, country, transport=api.transport(), **kwargs)


async def test_login_posts_verbatim_credentials_with_app_headers():
    api = MockAPI()
    api.on("POST", LOGIN, json_body=fixture("login_ok"))
    async with make_client(api, password=" pass word ", country="gb") as client:
        await client.authenticate()

    [request] = api.requests
    assert str(request.url) == "https://home-api.eufylife.com/v1/user/v2/email/login/"
    body = json.loads(request.content)
    assert (body["email"], body["password"]) == ("me@example.com", " pass word ")
    assert (body["client_id"], body["ab"]) == (CLIENT_ID, "gb")
    assert request.headers["country"] == "GB"
    assert request.headers["user-agent"] == f"EufyLife-Android-{APP_VERSION}"
    assert "token" not in request.headers


async def test_login_loads_members():
    api = MockAPI()
    api.on("POST", LOGIN, json_body=fixture("login_ok"))
    async with make_client(api) as client:
        await client.authenticate()
        members = await client.get_members()
    assert [(m.id, m.name, m.is_default) for m in members] == [
        ("cust-ann", "Ann Lee", True),
        ("cust-bob", "Bob", False),
    ]


async def test_login_without_customers_has_no_members():
    api = MockAPI()
    body = {k: v for k, v in fixture("login_ok").items() if k != "customers"}
    api.on("POST", LOGIN, json_body=body)
    async with make_client(api) as client:
        await client.authenticate()
        assert await client.get_members() == []


async def test_rejected_login_carries_code_and_message():
    api = MockAPI()
    api.on("POST", LOGIN, json_body=fixture("login_bad_credentials"))
    async with make_client(api) as client:
        with pytest.raises(LoginRejectedError) as info:
            await client.authenticate()
    assert info.value.code == 5002
    assert info.value.message.startswith("Incorrect email login or password")
    assert "code 5002" in str(info.value)


async def test_http_401_on_login():
    api = MockAPI()
    api.on("POST", LOGIN, status=401, json_body={"error": "Unauthorized"})
    async with make_client(api) as client:
        with pytest.raises(AuthenticationError):
            await client.authenticate()


@pytest.mark.parametrize("header, expected", [({"Retry-After": "30"}, 30), ({}, None)])
async def test_rate_limit_on_login(header, expected):
    api = MockAPI()
    api.on("POST", LOGIN, status=429, json_body={}, headers=header)
    async with make_client(api) as client:
        with pytest.raises(RateLimitError) as info:
            await client.authenticate()
    assert info.value.retry_after == expected


async def test_server_error_on_login():
    api = MockAPI()
    api.on("POST", LOGIN, status=503, text="unavailable")
    async with make_client(api) as client:
        with pytest.raises(APIError) as info:
            await client.authenticate()
    assert info.value.status == 503


@pytest.mark.parametrize(
    "exc, kind",
    [
        (httpx2.ConnectError("dns"), "ConnectError"),
        (httpx2.ReadTimeout("slow"), "ReadTimeout"),
    ],
)
async def test_network_errors_on_login(exc, kind):
    api = MockAPI()
    api.on("POST", LOGIN, raises=exc)
    async with make_client(api) as client:
        with pytest.raises(NetworkError) as info:
            await client.authenticate()
    assert info.value.kind == kind


@pytest.mark.parametrize(
    "body",
    [
        {"res_code": 1, "user_id": "u"},
        {"res_code": 1, "access_token": "t"},
        {"res_code": 1, "access_token": "t", "user_id": "u", "customers": [{"name": "no id"}]},
        {"res_code": 1, "access_token": "t", "user_id": "u", "customers": "nope"},
        ["not", "an", "object"],
    ],
)
async def test_login_payload_missing_token_user_or_members(body):
    api = MockAPI()
    api.on("POST", LOGIN, json_body=body)
    async with make_client(api) as client:
        with pytest.raises(ResponseShapeError) as info:
            await client.authenticate()
    assert info.value.call == "authenticate"


async def test_login_non_json_body():
    api = MockAPI()
    api.on("POST", LOGIN, text="<html>maintenance</html>")
    async with make_client(api) as client:
        with pytest.raises(ResponseShapeError):
            await client.authenticate()


async def test_session_expires_before_stated_lifetime():
    now = [1_000_000.0]
    api = MockAPI()
    api.on("POST", LOGIN, json_body={**fixture("login_ok"), "expires_in": 3600})
    async with make_client(api, clock=lambda: now[0]) as client:
        await client.authenticate()
        await client.get_members()

        now[0] += 3600 - 301
        await client.get_members()
        now[0] += 2  # inside the 5-minute margin
        with pytest.raises(AuthenticationError, match="expired"):
            await client.get_members()


async def test_aclose_closes_http_client():
    client = make_client(MockAPI())
    await client.aclose()
    assert client._http.is_closed
