"""Extract partition/app metadata without dumping credential-bearing flash strings."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def text(raw):
    return raw.split(b"\0", 1)[0].decode("utf-8", errors="replace")


def inspect(path):
    data = path.read_bytes()
    if len(data) != 16777216 or data[0] != 0xE9:
        raise ValueError("Expected a full 16MiB ESP32-S3 image with bootloader at offset zero")
    result = {"file":path.name,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"partitions":[]}
    for pos in range(0x8000, 0x9000, 32):
        entry = data[pos:pos + 32]
        magic, kind, subtype, offset, size, label, flags = struct.unpack("<HBBII16sI", entry)
        if magic != 0x50AA:
            break
        if offset + size > len(data):
            raise ValueError("Partition extends beyond flash")
        part = {"name":text(label),"type":kind,"subtype":subtype,"offset":hex(offset),"bytes":size,"flags":flags}
        desc = offset + 32
        if kind == 0 and data[offset] == 0xE9 and data[desc:desc + 4] == b"\x32\x54\xcd\xab":
            part["application"] = {"version":text(data[desc+16:desc+48]),
                                   "project":text(data[desc+48:desc+80]),
                                   "time":text(data[desc+80:desc+96]),
                                   "date":text(data[desc+96:desc+112]),
                                   "idf":text(data[desc+112:desc+144]),
                                   "elf_sha256":data[desc+144:desc+176].hex()}
        result["partitions"].append(part)
    if not result["partitions"]:
        raise ValueError("No valid partition table at expected 0x8000")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(inspect(args.file), indent=2) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    print(result)
