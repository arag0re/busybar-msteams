"""Native blue racing-current background for the upcoming-meeting screen.

The high-effort blue current and moving-spark treatment adapts
``effort_animation.py`` from https://github.com/wowlocal/busy-codex.
"""
from __future__ import annotations

from functools import lru_cache
import math
import struct

WIDTH = 72
HEIGHT = 16
FPS = 25
FRAME_COUNT = 125
ANIMATION_FILENAME = "upcoming_countdown.anim"
_BASE = (4, 16, 48)
_ACCENT = (35, 100, 245)
_EFFECT_RANK = 4
_MAX_BLOCKS = 127


def _frame(frame_index: int) -> bytes:
    phase = (frame_index % FRAME_COUNT) / FRAME_COUNT
    pixels = bytearray(WIDTH * HEIGHT * 4)
    for y in range(HEIGHT):
        edge = (abs(y - 7.5) / 7.5) ** 1.6
        field = 0.38 + 0.62 * edge
        for x in range(WIDTH):
            wave = 0.5 + 0.5 * math.sin(
                x * 0.085 - 2 * math.pi * phase + y * 0.18
            )
            intensity = 0.12 + 0.26 * wave
            streams = (
                0.5
                + 0.5
                * math.sin(x * 0.16 + y * 0.45 - 2 * math.pi * phase)
            ) ** 5
            intensity += 0.35 * streams

            spark = 0.0
            for k, lane in enumerate((0, 15, 1)):
                head = WIDTH / 2 + (WIDTH / 2 - 8) * math.sin(
                    2 * math.pi * phase + k * 2 * math.pi / 3
                )
                distance = math.hypot(x - head, y - lane)
                if distance < 12:
                    spark = max(
                        spark,
                        math.exp(-((distance / 4) ** 2))
                        * (0.2 + _EFFECT_RANK * 0.11),
                    )

            rgb = tuple(
                min(255, round(base + accent * intensity * field + spark * boost))
                for base, accent, boost in zip(_BASE, _ACCENT, (160, 190, 210))
            )
            offset = (y * WIDTH + x) * 4
            blue, green, red = rgb[2], rgb[1], rgb[0]
            pixels[offset : offset + 4] = bytes((blue, green, red, 255))
    return bytes(pixels)


def _compress_blocks(data: bytes, block_size: int = 4) -> bytes:
    blocks = [
        data[index : index + block_size]
        for index in range(0, len(data), block_size)
    ]
    encoded = bytearray()
    literals: list[bytes] = []

    def flush_literals() -> None:
        for index in range(0, len(literals), _MAX_BLOCKS):
            chunk = literals[index : index + _MAX_BLOCKS]
            encoded.append(0x80 | len(chunk))
            encoded.extend(b"".join(chunk))
        literals.clear()

    index = 0
    while index < len(blocks):
        run = 1
        while (
            run < _MAX_BLOCKS
            and index + run < len(blocks)
            and blocks[index + run] == blocks[index]
        ):
            run += 1
        if run >= 3:
            flush_literals()
            encoded.extend((run,))
            encoded.extend(blocks[index])
        else:
            literals.extend(blocks[index : index + run])
        index += run
    flush_literals()
    return bytes(encoded)


@lru_cache(maxsize=1)
def build_countdown_animation() -> bytes:
    """Build the looping 72x16 firmware animation in memory once per process."""
    frames = [_frame(index) for index in range(FRAME_COUNT)]
    frame_data = bytearray()
    max_frame_size = 0
    for frame in frames:
        compressed = _compress_blocks(frame)
        encoding, payload = (
            (1, compressed) if len(compressed) < len(frame) else (0, frame)
        )
        max_frame_size = max(max_frame_size, len(payload))
        frame_data.extend(struct.pack("<BBH", encoding, 1, len(payload)))
        frame_data.extend(payload)

    section_name = b"default\0"
    header_size = 36
    section_size = 13 + len(section_name)
    section = struct.pack(
        "<IIIB",
        0,
        FRAME_COUNT - 1,
        header_size + section_size,
        1,
    ) + section_name
    header = struct.pack(
        "<8sBBBBBHxIIIII",
        b"bicycle0",
        0,
        WIDTH,
        HEIGHT,
        2,
        FPS,
        max_frame_size,
        len(section),
        len(frame_data),
        1,
        FRAME_COUNT,
        FRAME_COUNT,
    )
    return bytes(header + section + frame_data)
