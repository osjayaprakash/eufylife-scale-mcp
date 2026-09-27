"""Pydantic models for the EufyLife payloads this server reads."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _Model(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True, extra="ignore")


class Member(_Model):
    """A person profile ("customer") on the EufyLife account."""

    id: str
    name: str = ""
    is_default: bool = Field(default=False, alias="default")


def _zero_if_missing(value: Any) -> Any:
    return 0 if value is None else value


class ScaleData(_Model):
    """Raw `scale_data` of one weigh-in. The scale reports 0 for metrics it did not measure."""

    weight: float = 0  # tenths of a kilogram
    bmi: float = 0
    body_fat: float = 0  # %
    body_fat_mass: float = 0  # kg
    subcutaneous_fat_rate: float = 0  # %
    visceral_fat: float = 0  # level
    muscle: float = 0  # %
    muscle_mass: float = 0  # kg
    skeletal_muscle_mass: float = 0  # kg
    fat_free_weight: float = 0  # kg
    bone_mass: float = 0  # kg
    water: float = 0  # %
    protein_ratio: float = 0  # %
    bmr: float = 0  # kcal/day
    body_age: float = 0  # years
    heart_rate: float = 0  # bpm

    @field_validator("*", mode="before")
    @classmethod
    def _null_is_zero(cls, value: Any) -> Any:
        return _zero_if_missing(value)


class Measurement(_Model):
    id: str
    device_id: str = ""
    customer_id: str
    product_code: str = ""
    time: datetime = Field(alias="create_time")  # UTC
    scale_data: ScaleData

    @field_validator("time", mode="before")
    @classmethod
    def _parse_epoch(cls, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ValueError("create_time must be a Unix timestamp")
        return datetime.fromtimestamp(value, UTC)
