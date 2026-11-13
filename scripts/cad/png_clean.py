"""Strip textual metadata from PNG files (standard library only).

FreeCAD's saveImage() embeds a Title chunk holding the absolute path of the file it wrote, plus an
XML view description. Rendered review images are published, so those chunks must not survive:
the path names the account and directory layout of the machine that built the model.
Pixel data, size and resolution chunks are kept untouched.
"""
import struct

SIGNATURE = b"\x89PNG\r\n\x1a\n"
DROP = {b"tEXt", b"zTXt", b"iTXt", b"eXIf", b"tIME"}


def strip_png_metadata(path):
    """Rewrite *path* without text/EXIF/time chunks. Returns True if anything was removed."""
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:8] != SIGNATURE:
        raise ValueError(f"Not a PNG file: {path}")
    kept, pos = [data[:8]], 8
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError(f"Truncated PNG chunk in {path}")
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        end = pos + 12 + length
        if end > len(data):
            raise ValueError(f"Truncated PNG chunk in {path}")
        if kind not in DROP:
            kept.append(data[pos:end])
        pos = end
    cleaned = b"".join(kept)
    if cleaned == data:
        return False
    with open(path, "wb") as handle:
        handle.write(cleaned)
    return True
