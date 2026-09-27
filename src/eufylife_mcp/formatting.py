"""Convert core models into JSON-serialisable dicts for tool results."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from eufylife_mcp.core import Measurement, Member

_LB_PER_KG = 2.2046226218

# (output key, scale_data field). Weight is handled separately: the API reports tenths of a kg.
_METRICS = (
    ("bmi", "bmi"),
    ("body_fat_pct", "body_fat"),
    ("body_fat_mass_kg", "body_fat_mass"),
    ("subcutaneous_fat_pct", "subcutaneous_fat_rate"),
    ("visceral_fat_level", "visceral_fat"),
    ("muscle_pct", "muscle"),
    ("muscle_mass_kg", "muscle_mass"),
    ("skeletal_muscle_mass_kg", "skeletal_muscle_mass"),
    ("fat_free_mass_kg", "fat_free_weight"),
    ("bone_mass_kg", "bone_mass"),
    ("water_pct", "water"),
    ("protein_pct", "protein_ratio"),
    ("bmr_kcal", "bmr"),
    ("body_age_years", "body_age"),
    ("heart_rate_bpm", "heart_rate"),
)


def member_to_dict(member: Member) -> dict[str, Any]:
    return {"member_id": member.id, "name": member.name, "is_default": member.is_default}


def measurement_to_dict(measurement: Measurement) -> dict[str, Any]:
    """Only metrics the scale measured are included; it reports 0 for the rest."""
    data = measurement.scale_data
    result: dict[str, Any] = {
        "measurement_id": measurement.id,
        "timestamp_utc": measurement.time.isoformat(),
    }
    if data.weight:
        kg = data.weight / 10
        result["weight_kg"] = round(kg, 2)
        result["weight_lb"] = round(kg * _LB_PER_KG, 1)
    for key, name in _METRICS:
        value = getattr(data, name)
        if value:
            result[key] = _number(value)
    return result


def _number(value: float) -> int | float:
    """Round to 2 places; whole numbers (bmr, body age, levels) become ints."""
    rounded = round(value, 2)
    return int(rounded) if rounded.is_integer() else rounded


def latest_response(
    member: Member, measurement: Measurement, *, now: datetime | None = None
) -> dict[str, Any]:
    reading = measurement_to_dict(measurement)
    elapsed = (now or datetime.now(UTC)) - measurement.time
    reading["age_hours"] = int(elapsed.total_seconds() // 3600)
    return {"member": member_to_dict(member), "measurement": reading}


def history_response(
    member: Member, measurements: Iterable[Measurement], *, days: int
) -> dict[str, Any]:
    ordered = sorted(measurements, key=lambda m: m.time)
    return {
        "member": member_to_dict(member),
        "days": days,
        "count": len(ordered),
        "measurements": [measurement_to_dict(m) for m in ordered],
    }
