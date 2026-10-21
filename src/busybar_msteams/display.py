from __future__ import annotations

from datetime import datetime

from busylib import types

from busybar_msteams.models import ScreenMode, ScreenState, format_countdown

APP_NAME = "busybar-msteams"
ANIMATION_PRIORITY = 90
STATIC_DISPLAY_PRIORITY = 100

COLORS = {
    ScreenMode.ON_CALL: ("#B00020FF", "#FFFFFFFF"),
    ScreenMode.LUNCH: ("#B85C00FF", "#FFFFFFFF"),
    ScreenMode.MEETING: ("#0067B8FF", "#FFFFFFFF"),
    ScreenMode.UPCOMING: ("#0067B8FF", "#FFFFFFFF"),
    ScreenMode.IDLE: ("#123524FF", "#FFFFFFFF"),
    ScreenMode.ERROR: ("#7A2400FF", "#FFFFFFFF"),
}

UPCOMING_PULSE_COLORS = ("#00508FFF", "#0067B8FF")


def build_payload(state: ScreenState, now: datetime) -> types.DisplayElements:
    background, foreground = COLORS[state.mode]
    subject = state.meeting.subject if state.meeting else "Microsoft Teams"
    on_call = state.mode is ScreenMode.ON_CALL

    if on_call:
        front = "ON CALL"
        title = "TEAMS · LIVE"
        detail = "Do not disturb"
    elif state.mode is ScreenMode.LUNCH:
        front = "LUNCH"
        title = "LUNCH BREAK"
        detail = "Enjoy your break"
    elif state.mode is ScreenMode.MEETING:
        front = "MEETING"
        title = "SCHEDULED MEETING"
        detail = "Calendar event in progress"
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
        elements.append(
            types.AnimationElement(
                id="front-on-call-animation",
                type="animation",
                stock_path="shared/on_call_72x16.anim",
                section="loop",
                loop=True,
                display=types.DisplayName.FRONT,
            )
        )
    elif state.mode is ScreenMode.LUNCH:
        elements.append(
            types.AnimationElement(
                id="front-lunch-animation",
                type="animation",
                stock_path="shared/lunch_72x16.anim",
                section="loop",
                loop=True,
                display=types.DisplayName.FRONT,
            )
        )
    elif state.mode is ScreenMode.MEETING:
        elements.append(
            types.AnimationElement(
                id="front-meeting-animation",
                type="animation",
                stock_path="shared/meeting_72x16.anim",
                section="loop",
                loop=True,
                display=types.DisplayName.FRONT,
            )
        )
    else:
        front_background = background
        if state.mode is ScreenMode.UPCOMING:
            front_background = UPCOMING_PULSE_COLORS[(now.second // 2) % 2]
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
                    fill_colors=[front_background],
                    border_width=0,
                    border_color=front_background,
                    display=types.DisplayName.FRONT,
                ),
                types.TextElement(
                    id="front-status",
                    type="text",
                    x=36,
                    y=8,
                    align="center",
                    text=front,
                    font="bold" if state.mode is ScreenMode.UPCOMING else "normal",
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
        priority=(
            ANIMATION_PRIORITY
            if on_call or state.mode in {ScreenMode.LUNCH, ScreenMode.MEETING}
            else STATIC_DISPLAY_PRIORITY
        ),
        led_notification_color=background,
        elements=elements,
    )
