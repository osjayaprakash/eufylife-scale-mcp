"""Builders for real core models, using the API's JSON field names."""

from __future__ import annotations

from datetime import datetime

from eufylife_mcp.core import Measurement, Member


def make_member(member_id: str, name: str, *, default: bool = False) -> Member:
    return Member.model_validate({"id": member_id, "name": name, "default": default})


def make_measurement(
    member: Member, when: datetime, weight_kg: float, *, record_id: str = "rec", **scale_data
) -> Measurement:
    """`when` must be timezone-aware; `scale_data` adds raw metrics (e.g. body_fat=27.4)."""
    return Measurement.model_validate(
        {
            "id": record_id,
            "device_id": "dev-1",
            "customer_id": member.id,
            "product_code": "T9148",
            "create_time": int(when.timestamp()),
            "scale_data": {"weight": round(weight_kg * 10), **scale_data},
        }
    )


ANN = make_member("cust-ann", "Ann Lee", default=True)
BOB = make_member("cust-bob", "Bob")
ANN_SMITH = make_member("cust-ann-smith", "Ann Smith")
