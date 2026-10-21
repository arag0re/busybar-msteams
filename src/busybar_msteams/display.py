from __future__ import annotations

from datetime import datetime

from busylib import types

from busybar_msteams.models import ScreenMode, ScreenState, format_countdown

APP_NAME = "busybar-msteams"

COLORS = {
    ScreenMode.ON_CALL: ("#B00020FF", "#FFFFFFFF"),
    ScreenMode.UPCOMING: ("#0067B8FF", "#FFFFFFFF"),
    ScreenMode.IDLE: ("#123524FF", "#FFFFFFFF"),
    ScreenMode.ERROR: ("#7A2400FF", "#FFFFFFFF"),
}


def build_payload(state: ScreenState, now: datetime) -> types.DisplayElements:
    background, foreground = COLORS[state.mode]
    subject = state.meeting.subject if state.meeting else "Microsoft Teams"
    on_call = state.mode is ScreenMode.ON_CALL

    if on_call:
        front = "ON CALL"
        title = "TEAMS · LIVE"
        detail = "Do not disturb"
    elif state.mode is ScreenMode.UPCOMING and state.meeting:
        countdown = format_countdown(state.meeting.start, now)
        front = f"NEXT {countdown}"
        title = "NEXT TEAMS"
        local_start = state.meeting.start.astimezone().strftime("%H:%M")
        detail = f"{local_start} · starts in {countdown}"
    elif state.mode is ScreenMode.ERROR:
        front = "SYNC ERR"
        title = "MICROSOFT GRAPH"
        subject = state.message or "Unable to update Teams status"
        detail = "Will retry automatically"
    else:
        front = "NO CALLS"
        title = "TEAMS"
        subject = "No upcoming Teams meetings"
        activity = state.presence.activity if state.presence else "unknown"
        detail = f"Current activity: {activity}"

    elements: list[types.DisplayElement] = []
    if on_call:
        palette = (
            "#FF2600FF",
            "#FF4A00FF",
            "#FF7400FF",
            "#FF9A00FF",
            "#FF7400FF",
            "#FF4A00FF",
        )
        phase = int(now.timestamp()) % len(palette)
        elements.append(
            types.RectangleElement(
                id="front-background",
                type="rectangle",
                x=0,
                y=0,
                width=72,
                height=16,
                fill="solid",
                fill_colors=[palette[0]],
                border_width=0,
                border_color=palette[0],
                display=types.DisplayName.FRONT,
            )
        )
        elements.extend(
            types.RectangleElement(
                id=f"front-dot-{row}-{column}",
                type="rectangle",
                x=column * 4 + 1,
                y=row * 4 + 1,
                width=2,
                height=2,
                fill="solid",
                fill_colors=[
                    palette[(column + row * 2 + phase) % len(palette)]
                ],
                border_width=0,
                border_color=palette[(column + row * 2 + phase) % len(palette)],
                display=types.DisplayName.FRONT,
            )
            for row in range(4)
            for column in range(18)
        )
        elements.extend(
            [
                types.RectangleElement(
                    id="front-microphone-head",
                    type="rectangle",
                    x=8,
                    y=2,
                    width=6,
                    height=8,
                    fill="solid",
                    fill_colors=[foreground],
                    border_width=0,
                    border_color=foreground,
                    display=types.DisplayName.FRONT,
                ),
                types.RectangleElement(
                    id="front-microphone-grille",
                    type="rectangle",
                    x=10,
                    y=4,
                    width=2,
                    height=4,
                    fill="solid",
                    fill_colors=[palette[(phase + 2) % len(palette)]],
                    border_width=0,
                    border_color=palette[(phase + 2) % len(palette)],
                    display=types.DisplayName.FRONT,
                ),
                types.RectangleElement(
                    id="front-microphone-stem",
                    type="rectangle",
                    x=10,
                    y=10,
                    width=2,
                    height=2,
                    fill="solid",
                    fill_colors=[foreground],
                    border_width=0,
                    border_color=foreground,
                    display=types.DisplayName.FRONT,
                ),
                types.RectangleElement(
                    id="front-microphone-base",
                    type="rectangle",
                    x=7,
                    y=12,
                    width=8,
                    height=1,
                    fill="solid",
                    fill_colors=[foreground],
                    border_width=0,
                    border_color=foreground,
                    display=types.DisplayName.FRONT,
                ),
                types.TextElement(
                    id="front-status",
                    type="text",
                    x=47,
                    y=8,
                    align="center",
                    text=front,
                    font="normal",
                    color=foreground,
                    display=types.DisplayName.FRONT,
                ),
            ]
        )
    else:
        elements.extend(
            [
                types.RectangleElement(
                    id="front-background",
                    type="rectangle",
                    x=0,
                    y=0,
                    width=72,
                    height=16,
                    fill="solid",
                    fill_colors=[background],
                    border_width=0,
                    border_color=background,
                    display=types.DisplayName.FRONT,
                ),
                types.TextElement(
                    id="front-status",
                    type="text",
                    x=36,
                    y=8,
                    align="center",
                    text=front,
                    font="normal",
                    color=foreground,
                    display=types.DisplayName.FRONT,
                ),
            ]
        )
    elements.extend(
        [
            types.RectangleElement(
                id="back-background",
                type="rectangle",
                x=0,
                y=0,
                width=160,
                height=80,
                fill="solid",
                fill_colors=[background],
                border_width=0,
                border_color=background,
                display=types.DisplayName.BACK,
            ),
            types.TextElement(
                id="back-title",
                type="text",
                x=4,
                y=8,
                text=title,
                font="small",
                color=foreground,
                display=types.DisplayName.BACK,
            ),
            types.TextElement(
                id="back-subject",
                type="text",
                x=4,
                y=35,
                text=subject,
                font="normal",
                color=foreground,
                width=152,
                scroll_rate=1000,
                scroll_start_delay=1500,
                scroll_repeat_delay=1000,
                display=types.DisplayName.BACK,
            ),
            types.TextElement(
                id="back-detail",
                type="text",
                x=4,
                y=67,
                text=detail,
                font="small",
                color=foreground,
                width=152,
                scroll_rate=1000,
                display=types.DisplayName.BACK,
            ),
        ]
    )
    return types.DisplayElements(
        application_name=APP_NAME,
        priority=90 if state.mode is ScreenMode.ON_CALL else 50,
        led_notification_color=background,
        elements=elements,
    )
