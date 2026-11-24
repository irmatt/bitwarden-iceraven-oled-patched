#!/usr/bin/env python3
"""Generate an original repo icon (no external artwork or trademarks)."""
import struct
import zlib

W = H = 512
BG = (16, 20, 26)
GREEN = (61, 220, 132)


def in_round_rect(x, y, x0, y0, x1, y1, r):
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return False
    cx = x0 + r if x < x0 + r else (x1 - r if x > x1 - r else x)
    cy = y0 + r if y < y0 + r else (y1 - r if y > y1 - r else y)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2


def in_poly(x, y, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


SHIELD = [(256, 96), (384, 150), (384, 286), (256, 400), (128, 286), (128, 150)]

rows = []
for y in range(H):
    row = bytearray()
    for x in range(W):
        color = BG
        if in_round_rect(x, y, 8, 8, 504, 504, 80) and not in_round_rect(x, y, 24, 24, 488, 488, 66):
            color = GREEN
        if in_poly(x, y, SHIELD):
            color = GREEN
            if (x - 256) ** 2 + (y - 232) ** 2 <= 30 ** 2 or (242 <= x <= 270 and 232 <= y <= 306):
                color = BG
        row += bytes(color)
    rows.append(bytes(row))

raw = b"".join(b"\x00" + r for r in rows)


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(raw, 9))
png += chunk(b"IEND", b"")
open("fdroid/repo/icons/icon.png", "wb").write(png)
print(f"wrote fdroid/repo/icons/icon.png ({len(png)} bytes, {W}x{H})")
