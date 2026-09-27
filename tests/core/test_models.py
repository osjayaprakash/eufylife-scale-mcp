from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from eufylife_mcp.core import Measurement, Member, ScaleData

RECORD = {
    "id": "rec-1",
    "device_id": "dev-1",
    "customer_id": "cust-ann",
    "create_time": 1790326800,
    "product_code": "T9148",
    "scale_data": {"weight": 652, "body_fat": 27.4, "impedance": 512},
}


def test_member_from_api_keys_strips_name():
    member = Member.model_validate({"id": "cust-ann", "name": " Ann ", "default": True, "sex": "f"})
    assert (member.id, member.name, member.is_default) == ("cust-ann", "Ann", True)


def test_member_defaults():
    member = Member.model_validate({"id": "cust-x"})
    assert (member.name, member.is_default) == ("", False)


def test_measurement_time_is_utc():
    m = Measurement.model_validate(RECORD)
    assert m.time == datetime(2026, 9, 25, 9, 0, tzinfo=UTC)


def test_scale_data_defaults_and_nulls_are_zero():
    data = ScaleData.model_validate({"weight": 652, "bmi": None})
    assert (data.weight, data.bmi, data.muscle_mass) == (652, 0, 0)


@pytest.mark.parametrize("raw", ["yesterday", None, True])
def test_bad_create_time_is_a_validation_error(raw):
    with pytest.raises(ValidationError):
        Measurement.model_validate({**RECORD, "create_time": raw})
