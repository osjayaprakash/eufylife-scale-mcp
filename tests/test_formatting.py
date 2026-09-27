import json
from datetime import UTC, datetime

from eufylife_mcp.formatting import (
    history_response,
    latest_response,
    measurement_to_dict,
    member_to_dict,
)
from tests.factories import ANN, make_measurement

MORNING = datetime(2026, 9, 26, 7, 0, tzinfo=UTC)


def test_member_to_dict():
    assert member_to_dict(ANN) == {"member_id": "cust-ann", "name": "Ann Lee", "is_default": True}


def test_weight_is_converted_from_tenths_of_kg():
    d = measurement_to_dict(make_measurement(ANN, MORNING, 65.2, record_id="r1"))
    assert d == {
        "measurement_id": "r1",
        "timestamp_utc": "2026-09-26T07:00:00+00:00",
        "weight_kg": 65.2,
        "weight_lb": 143.7,
    }


def test_body_composition_keys_carry_units():
    m = make_measurement(
        ANN, MORNING, 65.2, bmi=23.9, body_fat=27.4, muscle_mass=44.8, bmr=1380, visceral_fat=6
    )
    d = measurement_to_dict(m)
    assert (d["bmi"], d["body_fat_pct"], d["muscle_mass_kg"]) == (23.9, 27.4, 44.8)
    assert (d["bmr_kcal"], d["visceral_fat_level"]) == (1380, 6)
    assert isinstance(d["bmr_kcal"], int) and isinstance(d["bmi"], float)


def test_unmeasured_metrics_are_omitted():
    d = measurement_to_dict(make_measurement(ANN, MORNING, 65.2, body_fat=0, heart_rate=None))
    assert "body_fat_pct" not in d and "heart_rate_bpm" not in d


def test_missing_weight_is_omitted():
    d = measurement_to_dict(make_measurement(ANN, MORNING, 0, body_fat=20))
    assert "weight_kg" not in d and "weight_lb" not in d
    assert d["body_fat_pct"] == 20


def test_latest_reports_age_so_stale_values_are_visible():
    now = datetime(2026, 9, 27, 10, 30, tzinfo=UTC)
    result = latest_response(ANN, make_measurement(ANN, MORNING, 65.2), now=now)
    assert result["member"]["name"] == "Ann Lee"
    assert result["measurement"]["age_hours"] == 27


def test_history_sorts_oldest_first_and_counts():
    late = make_measurement(ANN, datetime(2026, 9, 26, tzinfo=UTC), 65.0)
    early = make_measurement(ANN, datetime(2026, 9, 1, tzinfo=UTC), 66.0)
    result = history_response(ANN, [late, early], days=30)
    assert (result["count"], result["days"]) == (2, 30)
    assert [r["weight_kg"] for r in result["measurements"]] == [66.0, 65.0]


def test_history_empty():
    result = history_response(ANN, [], days=7)
    assert result["count"] == 0
    assert result["measurements"] == []


def test_responses_are_json_serialisable():
    m = make_measurement(ANN, MORNING, 65.2, body_fat=27.4)
    json.dumps(history_response(ANN, [m], days=30))
    json.dumps(latest_response(ANN, m))
