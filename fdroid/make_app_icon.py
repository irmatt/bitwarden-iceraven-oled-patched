#!/usr/bin/env python3
"""Generate an original Bitwarden-rebuild app icon (no trademark artwork)."""
import struct
import zlib

W = H = 512
BLUE = (23, 93, 220)
WHITE = (245, 248, 255)
B_GLYPH = [
    "11111",
    "10001",
    "10001",
    "11111",
    "10001",
    "10001",
    "11111",
]


def in_round_rect(x, y, x0, y0, x1, y1, r):
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return False
    cx = x0 + r if x < x0 + r else (x1 - r if x > x1 - r else x)
    cy = y0 + r if y < y0 + r else (y1 - r if y > y1 - r else y)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2


rows = []
for y in range(H):
    row = bytearray()
    for x in range(W):
        color = BLUE if in_round_rect(x, y, 0, 0, 511, 511, 96) else (10, 14, 20)
        # centred 5x7 glyph, 48 px per cell
        gx = (x - 140) // 48
        gy = (y - 112) // 48
        if 0 <= gx < 5 and 0 <= gy < 7 and B_GLYPH[gy][gx] == "1":
            color = WHITE
        row += bytes(color)
    rows.append(bytes(row))

raw = b"".join(b"\x00" + r for r in rows)


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(raw, 9))
png += chunk(b"IEND", b"")
open("fdroid/repo/com.x8bit.bitwarden/en-US/icon.png", "wb").write(png)
print(f"wrote app icon ({len(png)} bytes)")
