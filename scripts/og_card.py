"""Per-hub Open Graph cards as PNG, stdlib only.

Every hub uses the same 1200×630 template. The title, count, and check date
are the only things that change, and they are drawn with an embedded bitmap
font so the Cloudflare Pages build does not need Pillow. The English hub name
is ASCII; Vietnamese titles stay in the HTML og:title and alt text.
"""
import struct
import zlib

W, H = 1200, 630

# 5×7 glyphs, bit 4 is the leftmost pixel. Public-domain shapes drawn for this file.
_G = {
    "A": (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "B": (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    "C": (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    "D": (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    "E": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    "F": (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    "G": (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    "H": (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    "I": (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "J": (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    "K": (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    "L": (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    "M": (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    "N": (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    "O": (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "P": (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    "Q": (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    "R": (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    "S": (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    "T": (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    "U": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    "V": (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    "W": (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b10101, 0b01010),
    "X": (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    "Y": (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    "Z": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    "0": (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    "1": (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    "2": (0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b01000, 0b11111),
    "3": (0b11110, 0b00001, 0b00001, 0b01110, 0b00001, 0b00001, 0b11110),
    "4": (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    "5": (0b11111, 0b10000, 0b10000, 0b11110, 0b00001, 0b00001, 0b11110),
    "6": (0b01110, 0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    "7": (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    "8": (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    "9": (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00001, 0b01110),
    "/": (0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    "-": (0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000),
    ".": (0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b01100, 0b01100),
    ":": (0b00000, 0b01100, 0b01100, 0b00000, 0b01100, 0b01100, 0b00000),
    "+": (0b00100, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0b00100),
    "&": (0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101),
    "#": (0b01010, 0b01010, 0b11111, 0b01010, 0b11111, 0b01010, 0b01010),
}


def _png(width, height, rgb):
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        raw.extend(rgb[y * stride:(y + 1) * stride])

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")


class _Canvas:
    def __init__(self, width, height, color):
        self.w = width
        self.h = height
        self.buf = bytearray(color * (width * height))

    def _put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = color

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            start = (yy * self.w + x0) * 3
            row = color * (x1 - x0)
            self.buf[start:start + len(row)] = row

    def circle(self, cx, cy, radius, color):
        r2 = radius * radius
        for y in range(max(0, cy - radius), min(self.h, cy + radius + 1)):
            for x in range(max(0, cx - radius), min(self.w, cx + radius + 1)):
                if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r2:
                    self._put(x, y, color)

    def text(self, x, y, text, scale, color):
        cursor = x
        for ch in text:
            if ch == " ":
                cursor += 3 * scale
                continue
            glyph = _G.get(ch)
            if not glyph:
                cursor += 4 * scale
                continue
            for row, bits in enumerate(glyph):
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(cursor + col * scale, y + row * scale, scale, scale, color)
            cursor += 6 * scale
        return cursor - x

    def png(self):
        return _png(self.w, self.h, self.buf)


def _wrap(text, limit):
    words = (text or "").split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if len(trial) <= limit:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines[:3] or [""]


def render_hub_png(title, count, updated):
    """Return PNG bytes for one hub card."""
    ink = bytes((11, 17, 32))
    teal = bytes((15, 118, 110))
    deep = bytes((15, 61, 58))
    mint = bytes((94, 234, 212))
    white = bytes((255, 255, 255))
    muted = bytes((203, 213, 225))
    canvas = _Canvas(W, H, ink)
    canvas.circle(1040, 150, 260, deep)
    canvas.circle(1120, 520, 180, bytes((17, 49, 47)))
    canvas.rect(0, 0, 18, H, teal)
    canvas.rect(0, H - 64, W, 64, teal)
    canvas.rect(72, 64, 72, 72, teal)
    canvas.text(84, 78, "RJ", 5, white)
    canvas.text(164, 72, "REMOTEJOB", 4, white)
    canvas.text(164 + 10 * 6 * 4, 72, "VN", 4, mint)
    label = "".join(ch if ch in _G or ch == " " else " " for ch in (title or "JOBS").upper())
    label = " ".join(label.split()) or "JOBS"
    scale = 8 if len(label) <= 14 else 6 if len(label) <= 22 else 5
    limit = 16 if scale >= 8 else 22 if scale == 6 else 28
    y = 180
    for line in _wrap(label, limit):
        canvas.text(72, y, line, scale, white)
        y += scale * 8 + 8
    count_text = f"{int(count)} OPEN JOBS"
    canvas.text(72, min(y + 28, 430), count_text, 6, mint)
    if updated:
        canvas.text(72, 520, f"UPDATED {updated}", 4, muted)
    canvas.text(72, 582, "REMOTEJOB.NGUYENQUOCDAT.DEV", 3, white)
    return canvas.png()


def write_hub_png(path, title, count, updated):
    data = render_hub_png(title, count, updated)
    with open(path, "wb") as fh:
        fh.write(data)
    return True
