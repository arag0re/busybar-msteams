from datetime import UTC, datetime, timedelta

from busybar_msteams.display import (
    ANIMATION_PRIORITY,
    STATIC_DISPLAY_PRIORITY,
    build_payload,
)
from busybar_msteams.models import Meeting, ScreenMode, ScreenState, TeamsPresence


def test_on_call_payload_uses_stock_firmware_animation() -> None:
    now = datetime(2026, 8, 3, 10, tzinfo=UTC)
    state = ScreenState(
        ScreenMode.ON_CALL,
        presence=TeamsPresence("Busy", "InACall"),
    )
    payload = build_payload(state, now)
    dumped = payload.model_dump()
    assert dumped["priority"] == ANIMATION_PRIORITY
    assert dumped["led_notification_color"] == "#B00020FF"
    animation = next(
        element
        for element in dumped["elements"]
        if element.get("type") == "animation"
    )
    assert animation["id"] == "front-on-call-animation"
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
    assert payload["priority"] == STATIC_DISPLAY_PRIORITY
    front_text = next(
        element
        for element in payload["elements"]
        if element.get("id") == "front-status"
    )
    front_background = next(
        element
        for element in payload["elements"]
        if element.get("id") == "front-background"
    )
    assert front_text["text"] == "NEXT 2.1h"
    assert front_text["font"] == "bold"
    assert front_background["fill_colors"] == ["#00508FFF"]


def test_upcoming_countdown_pulses_between_blue_shades() -> None:
    now = datetime(2026, 8, 3, 10, tzinfo=UTC)
    state = ScreenState(
        ScreenMode.UPCOMING,
        meeting=Meeting(
            "1",
            "Roadmap",
            now + timedelta(hours=2),
            now + timedelta(hours=3),
        ),
    )
    payload = build_payload(state, now.replace(second=2)).model_dump()
    front_background = next(
        element
        for element in payload["elements"]
        if element.get("id") == "front-background"
    )
    assert front_background["fill_colors"] == ["#0067B8FF"]


def test_lunch_payload_uses_stock_firmware_animation() -> None:
    state = ScreenState(
        ScreenMode.LUNCH,
        meeting=Meeting(
            "lunch",
            "Lunch break",
            datetime(2026, 8, 3, 10, tzinfo=UTC),
            datetime(2026, 8, 3, 11, tzinfo=UTC),
            is_teams_meeting=False,
        ),
    )
    payload = build_payload(state, datetime(2026, 8, 3, 10, tzinfo=UTC)).model_dump()
    assert payload["priority"] == ANIMATION_PRIORITY
    animation = next(
        element
        for element in payload["elements"]
        if element.get("type") == "animation"
    )
    assert animation["stock_path"] == "shared/lunch_72x16.anim"
    assert animation["section"] == "loop"
    assert animation["loop"] is True


def test_scheduled_meeting_payload_uses_stock_firmware_animation() -> None:
    now = datetime(2026, 8, 3, 10, tzinfo=UTC)
    state = ScreenState(
        ScreenMode.MEETING,
        meeting=Meeting(
            "meeting",
            "Architecture review",
            now - timedelta(minutes=5),
            now + timedelta(minutes=25),
        ),
    )
    payload = build_payload(state, now).model_dump()
    assert payload["priority"] == ANIMATION_PRIORITY
    animation = next(
        element
        for element in payload["elements"]
        if element.get("type") == "animation"
    )
    assert animation["id"] == "front-meeting-animation"
    assert animation["stock_path"] == "shared/meeting_72x16.anim"
    assert animation["section"] == "loop"
    assert animation["loop"] is True
