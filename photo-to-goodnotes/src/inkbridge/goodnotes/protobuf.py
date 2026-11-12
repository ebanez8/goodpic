"""Protobuf wire editor preserving untouched field bytes and order."""

from dataclasses import dataclass


def varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("negative varint")
    out = bytearray()
    while value > 127:
        out.append((value & 127) | 128)
        value >>= 7
    out.append(value)
    return bytes(out)


def read_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    for shift in range(0, 70, 7):
        if offset >= len(data):
            raise ValueError("truncated varint")
        byte = data[offset]
        offset += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, offset
    raise ValueError("varint too long")


@dataclass(frozen=True)
class Field:
    number: int
    wire: int
    value: bytes | int
    raw: bytes


def fields(data: bytes) -> list[Field]:
    result = []
    offset = 0
    while offset < len(data):
        start = offset
        key, offset = read_varint(data, offset)
        number, wire = key >> 3, key & 7
        if not number:
            raise ValueError("invalid protobuf field zero")
        value: bytes | int
        if wire == 0:
            value, offset = read_varint(data, offset)
        elif wire == 2:
            length, offset = read_varint(data, offset)
            end = offset + length
            if end > len(data):
                raise ValueError("truncated protobuf bytes")
            value = data[offset:end]
            offset = end
        elif wire in (1, 5):
            end = offset + (8 if wire == 1 else 4)
            if end > len(data):
                raise ValueError("truncated protobuf fixed field")
            value = data[offset:end]
            offset = end
        else:
            raise ValueError(f"unsupported protobuf wire type {wire}")
        result.append(Field(number, wire, value, data[start:offset]))
    return result


def encode_field(number: int, wire: int, value: bytes | int) -> bytes:
    key = varint(number << 3 | wire)
    if wire == 0 and isinstance(value, int):
        return key + varint(value)
    if not isinstance(value, bytes):
        raise TypeError("byte field expected")
    return key + (varint(len(value)) if wire == 2 else b"") + value


def replace(data: bytes, number: int, value: bytes | int, *, wire: int | None = None) -> bytes:
    parts = []
    seen = False
    for field in fields(data):
        if field.number == number and not seen:
            parts.append(encode_field(number, field.wire if wire is None else wire, value))
            seen = True
        else:
            parts.append(field.raw)
    if not seen:
        if wire is None:
            raise ValueError(f"missing field {number}")
        parts.append(encode_field(number, wire, value))
    return b"".join(parts)


def first(data: bytes, number: int) -> bytes | int | None:
    return next((f.value for f in fields(data) if f.number == number), None)


def records(data: bytes) -> list[bytes]:
    result = []
    offset = 0
    while offset < len(data):
        length, offset = read_varint(data, offset)
        end = offset + length
        if end > len(data):
            raise ValueError("truncated page record")
        result.append(data[offset:end])
        offset = end
    return result


def pack_records(items: list[bytes]) -> bytes:
    return b"".join(varint(len(item)) + item for item in items)
