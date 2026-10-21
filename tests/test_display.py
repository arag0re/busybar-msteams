from datetime import UTC, datetime, timedelta
import struct

from busybar_msteams.countdown_animation import (
    ANIMATION_FILENAME,
    build_countdown_animation,
)
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
    animation = next(
        element
        for element in payload["elements"]
        if element.get("id") == "front-upcoming-animation"
    )
    assert front_text["text"] == "NEXT 2.1h"
    assert front_text["font"] == "bold"
    assert front_text["z_index"] == 10
    assert animation["type"] == "animation"
    assert animation["path"] == ANIMATION_FILENAME
    assert animation["section"] == "default"
    assert animation["loop"] is True
    assert animation["z_index"] == 0


def test_countdown_animation_is_native_72_by_16_loop() -> None:
    animation = build_countdown_animation()
    header = struct.unpack_from("<8sBBBBBHxIIIII", animation)

    assert header[0] == b"bicycle0"
    assert (header[2], header[3], header[5]) == (72, 16, 25)
    assert header[-2:] == (45, 45)
    frame_offset = 36 + header[7]
    assert frame_offset + header[8] == len(animation)

    offset = frame_offset
    total_duration = 0
    for _ in range(header[10]):
        encoding, duration, data_length = struct.unpack_from("<BBH", animation, offset)
        offset += 4
        frame_data = animation[offset : offset + data_length]
        offset += data_length
        assert duration > 0
        if encoding == 0:
            assert data_length == 72 * 16 * 4
        else:
            decoded = bytearray()
            cursor = 0
            while cursor < len(frame_data):
                opcode = frame_data[cursor]
                cursor += 1
                block_count = opcode & 0x7F
                if opcode & 0x80:
                    size = block_count * 4
                    decoded.extend(frame_data[cursor : cursor + size])
                    cursor += size
                else:
                    block = frame_data[cursor : cursor + 4]
                    decoded.extend(block * block_count)
                    cursor += 4
            assert len(decoded) == 72 * 16 * 4
        total_duration += duration

    assert offset == len(animation)
    assert total_duration == 45


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
