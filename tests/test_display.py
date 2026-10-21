from datetime import UTC, datetime, timedelta

from busybar_msteams.display import build_payload
from busybar_msteams.models import Meeting, ScreenMode, ScreenState, TeamsPresence


def test_on_call_payload_has_animated_mic_and_on_call_message() -> None:
    now = datetime(2026, 8, 3, 10, tzinfo=UTC)
    state = ScreenState(
        ScreenMode.ON_CALL,
        presence=TeamsPresence("Busy", "InACall"),
    )
    payload = build_payload(state, now)
    dumped = payload.model_dump()
    assert dumped["priority"] == 90
    assert dumped["led_notification_color"] == "#B00020FF"
    assert any(element.get("text") == "ON CALL" for element in dumped["elements"])
    assert any(
        element.get("id") == "front-microphone-head"
        for element in dumped["elements"]
    )

    next_frame = build_payload(state, now + timedelta(seconds=1)).model_dump()

    def colors(payload: dict) -> list[str]:
        return [
            element["fill_colors"][0]
            for element in payload["elements"]
            if element.get("id", "").startswith("front-dot-")
        ]

    assert colors(dumped) != colors(next_frame)


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
