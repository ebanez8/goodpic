"""Apple LZ4 block framing used by native Goodnotes geometry."""

import struct


def _decode_block(src: bytes, expected: int) -> bytes:
    out = bytearray()
    pos = 0
    while pos < len(src):
        token = src[pos]
        pos += 1
        literal = token >> 4
        if literal == 15:
            while True:
                extra = src[pos]
                pos += 1
                literal += extra
                if extra != 255:
                    break
        if pos + literal > len(src):
            raise ValueError("truncated LZ4 literal")
        out.extend(src[pos:pos + literal])
        pos += literal
        if pos == len(src):
            break
        if pos + 2 > len(src):
            raise ValueError("truncated LZ4 match")
        distance = int.from_bytes(src[pos:pos + 2], "little")
        pos += 2
        if not 0 < distance <= len(out):
            raise ValueError("invalid LZ4 match distance")
        length = token & 15
        if length == 15:
            while True:
                extra = src[pos]
                pos += 1
                length += extra
                if extra != 255:
                    break
        for _ in range(length + 4):
            out.append(out[-distance])
    if len(out) != expected:
        raise ValueError("LZ4 decoded size mismatch")
    return bytes(out)


def decompress(blob: bytes) -> bytes:
    out = bytearray()
    pos = 0
    while pos < len(blob):
        tag = blob[pos:pos + 4]
        pos += 4
        if tag == b"bv4$":
            if pos != len(blob):
                raise ValueError("trailing Apple LZ4 data")
            return bytes(out)
        if tag == b"bv41":
            size, compressed = struct.unpack_from("<II", blob, pos)
            pos += 8
            out.extend(_decode_block(blob[pos:pos + compressed], size))
            pos += compressed
        elif tag == b"bv4-":
            size = struct.unpack_from("<I", blob, pos)[0]
            pos += 4
            out.extend(blob[pos:pos + size])
            pos += size
        else:
            raise ValueError("unknown Apple LZ4 chunk")
        if pos > len(blob):
            raise ValueError("truncated Apple LZ4 chunk")
    raise ValueError("missing Apple LZ4 terminator")


def _length_extra(length: int) -> bytes:
    extra = bytearray()
    while length >= 255:
        extra.append(255)
        length -= 255
    extra.append(length)
    return bytes(extra)


def _encode_block(raw: bytes) -> bytes:
    """Encode ordinary LZ4 matches; leave five final bytes as literals."""
    out = bytearray()
    seen: dict[bytes, int] = {}
    anchor = pos = 0
    limit = len(raw) - 12
    while pos <= limit:
        key = raw[pos:pos + 4]
        previous = seen.get(key)
        seen[key] = pos
        if previous is None or pos - previous > 65535:
            pos += 1
            continue
        length = 4
        while pos + length < len(raw) - 5 and raw[previous + length] == raw[pos + length]:
            length += 1
        literals = raw[anchor:pos]
        out.append((min(len(literals), 15) << 4) | min(length - 4, 15))
        if len(literals) >= 15:
            out.extend(_length_extra(len(literals) - 15))
        out.extend(literals)
        out.extend((pos - previous).to_bytes(2, "little"))
        if length - 4 >= 15:
            out.extend(_length_extra(length - 4 - 15))
        end = pos + length
        pos += 1
        while pos < end:
            if pos + 4 <= len(raw):
                seen[raw[pos:pos + 4]] = pos
            pos += 1
        anchor = pos
    literals = raw[anchor:]
    out.append(min(len(literals), 15) << 4)
    if len(literals) >= 15:
        out.extend(_length_extra(len(literals) - 15))
    out.extend(literals)
    return bytes(out)


def compress(raw: bytes) -> bytes:
    """Encode Apple-framed LZ4 with compressed blocks only when smaller."""
    if not raw:
        return b"bv4$"
    chunks = []
    for start in range(0, len(raw), 65536):
        part = raw[start:start + 65536]
        block = _encode_block(part)
        if len(block) < len(part):
            chunks.append(b"bv41" + struct.pack("<II", len(part), len(block)) + block)
        else:
            chunks.append(b"bv4-" + struct.pack("<I", len(part)) + part)
    return b"".join(chunks) + b"bv4$"
