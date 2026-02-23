from __future__ import annotations

from piccolo.columns.column_types import JSONB, Numeric, Timestamptz, Varchar
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.table import Table


class PredictionRecord(Table):
    risk_level = Varchar(length=16)
    confidence = Numeric(digits=(5, 4))
    feature_importance = JSONB()
    input_payload = JSONB()
    created_at = Timestamptz(default=TimestamptzNow())

