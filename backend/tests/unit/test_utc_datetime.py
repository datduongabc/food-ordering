from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy.dialects import sqlite

from app.core.db import UTCDateTime

DIALECT = sqlite.dialect()
VIETNAM = timezone(timedelta(hours=7))


def test_bind_converts_aware_datetimes_to_utc():
    local = datetime(2026, 10, 29, 19, 0, tzinfo=VIETNAM)

    stored = UTCDateTime().process_bind_param(local, DIALECT)

    assert stored == datetime(2026, 10, 29, 12, 0, tzinfo=UTC)


def test_bind_rejects_naive_datetimes():
    with pytest.raises(ValueError, match="Naive"):
        UTCDateTime().process_bind_param(datetime(2026, 10, 29, 12, 0), DIALECT)


def test_result_restores_utc_tzinfo_dropped_by_sqlite():
    loaded = UTCDateTime().process_result_value(datetime(2026, 10, 29, 12, 0), DIALECT)

    assert loaded.tzinfo is UTC


def test_none_passes_through():
    assert UTCDateTime().process_bind_param(None, DIALECT) is None
    assert UTCDateTime().process_result_value(None, DIALECT) is None
