from datetime import UTC, datetime

from app.modules.reservations import service


def test_today_follows_vietnam_time_not_utc(monkeypatch):
    # 23:30 UTC on the 29th is already 06:30 on the 30th in Ho Chi Minh City.
    monkeypatch.setattr(service, "utcnow", lambda: datetime(2026, 10, 29, 23, 30, tzinfo=UTC))

    policy = service.get_policy()

    assert str(policy.today) == "2026-10-30"
    assert str(policy.last_bookable_date) == "2026-11-02"
