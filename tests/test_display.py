from datetime import UTC, datetime, timedelta

from busybar_msteams.display import build_payload
from busybar_msteams.models import Meeting, ScreenMode, ScreenState, TeamsPresence


def test_on_call_payload_uses_stock_firmware_animation() -> None:
    now = datetime(2026, 8, 3, 10, tzinfo=UTC)
    state = ScreenState(
        ScreenMode.ON_CALL,
        presence=TeamsPresence("Busy", "InACall"),
    )
    payload = build_payload(state, now)
    dumped = payload.model_dump()
    assert dumped["priority"] == 90
    assert dumped["led_notification_color"] == "#B00020FF"
    animation = next(
        element
        for element in dumped["elements"]
        if element.get("type") == "animation"
    )
    assert animation["stock_path"] == "shared/on_call_72x16.anim"
    assert animation["section"] == "loop"
    assert animation["loop"] is True


def test_upcoming_payload_displays_countdown_in_hours() -> None:
    now = datetime(2026, 8, 3, 10, tzinfo=UTC)
    state = ScreenState(
        ScreenMode.UPCOMING,
        meeting=Meeting(
            "1",
            "Roadmap",
            now + timedelta(hours=2.01),
            now + timedelta(hours=3),
        ),
        presence=TeamsPresence("Available", "Available"),
    )
    payload = build_payload(state, now).model_dump()
    assert any(element.get("text") == "NEXT 2.1h" for element in payload["elements"])
