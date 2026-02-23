from __future__ import annotations

from piccolo.columns.column_types import Float, Timestamptz, Varchar
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.table import Table


class Vehicle(Table):
    name = Varchar(length=128)
    mileage = Float()
    engine_hours = Float()
    created_at = Timestamptz(default=TimestamptzNow())
