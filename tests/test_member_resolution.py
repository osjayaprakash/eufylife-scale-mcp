import pytest
from mcp.server.mcpserver.exceptions import ToolError

from eufylife_mcp.service import UnknownMemberError, resolve_member
from tests.factories import ANN, ANN_SMITH, BOB, make_member


@pytest.mark.parametrize("identifier", [None, "", "   "])
def test_blank_identifier_picks_only_member(identifier):
    assert resolve_member([BOB], identifier) is BOB


def test_blank_identifier_picks_default_member():
    assert resolve_member([BOB, ANN], None) is ANN


def test_blank_identifier_with_no_members():
    with pytest.raises(ToolError, match="no member profiles"):
        resolve_member([], None)


def test_blank_identifier_without_a_default_lists_members():
    with pytest.raises(ToolError) as info:
        resolve_member([BOB, ANN_SMITH], None)
    assert not isinstance(info.value, UnknownMemberError)
    assert "Bob (cust-bob)" in str(info.value)
    assert "Ann Smith" in str(info.value)


def test_member_id():
    assert resolve_member([ANN, BOB], "cust-bob") is BOB


def test_member_id_ignores_case():
    assert resolve_member([ANN, BOB], "CUST-BOB") is BOB


@pytest.mark.parametrize("identifier", ["ann lee", "ANN LEE", "  Ann   Lee "])
def test_full_name_is_case_and_whitespace_insensitive(identifier):
    assert resolve_member([ANN, BOB, ANN_SMITH], identifier) is ANN


def test_first_name_when_unique():
    assert resolve_member([ANN, BOB], "bob") is BOB


def test_full_name_wins_over_ambiguous_first_name():
    assert resolve_member([ANN, ANN_SMITH], "Ann Smith") is ANN_SMITH


def test_ambiguous_first_name_lists_candidates():
    with pytest.raises(ToolError, match="ambiguous") as info:
        resolve_member([ANN, ANN_SMITH, BOB], "ann")
    assert not isinstance(info.value, UnknownMemberError)
    assert "Ann Lee" in str(info.value) and "Ann Smith" in str(info.value)
    assert "Bob" not in str(info.value)


def test_unknown_name_is_unknown_member_error_listing_members():
    with pytest.raises(UnknownMemberError, match="'Zed'") as info:
        resolve_member([ANN], "Zed")
    assert "Ann Lee" in str(info.value)


def test_named_member_with_no_members_says_none():
    with pytest.raises(UnknownMemberError, match="Members on this account: none"):
        resolve_member([], "Ann")


def test_member_without_a_name_is_still_resolvable_by_id():
    nameless = make_member("cust-x", "")
    assert resolve_member([ANN, nameless], "cust-x") is nameless
    with pytest.raises(UnknownMemberError):
        resolve_member([ANN, nameless], "x")
