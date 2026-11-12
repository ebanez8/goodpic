"""Native Goodnotes pen insertion using a measured genuine pen topology."""

import struct
import uuid
from dataclasses import dataclass
from pathlib import Path

from inkbridge.core.models import InkDocument, Page, Stroke, StrokePoint
from inkbridge.goodnotes.archive import open_archive
from inkbridge.goodnotes.compression import compress, decompress
from inkbridge.goodnotes.geometry import sampled_points, transform
from inkbridge.goodnotes.protobuf import encode_field, fields, first, pack_records, records, replace
from inkbridge.goodnotes.reader import PenTemplate, choose_page, find_pen
from inkbridge.strokes.validation import validate


@dataclass(frozen=True)
class EncodeResult:
    path: Path
    page_member: str
    stroke_ids: list[str]
    decoded_points: list[list[tuple[float, float, float]]]


def _rgba(color: tuple[float, float, float, float]) -> bytes:
    return b"".join(encode_field(i, 5, struct.pack("<f", channel))
                    for i, channel in enumerate(color, 1))


def _fresh_id(used: set[bytes]) -> bytes:
    while True:
        value = str(uuid.uuid4()).upper().encode("ascii")
        if value not in used:
            used.add(value)
            return value


def _existing_ids(recs: list[bytes]) -> set[bytes]:
    used = set()
    for rec in recs:
        identifier = first(rec, 1)
        if isinstance(identifier, bytes):
            used.add(identifier)
        sub = first(rec, 7)
        if isinstance(sub, bytes):
            try:
                identifier = first(sub, 1)
                if isinstance(identifier, bytes):
                    used.add(identifier)
            except ValueError:
                pass
    return used


def _existing_tokens(recs: list[bytes]) -> set[int]:
    used: set[int] = set()
    for rec in recs:
        nested = first(rec, 2)
        if isinstance(nested, bytes):
            token = first(nested, 2)
            if isinstance(token, int):
                used.add(token)
        sub = first(rec, 7)
        if isinstance(sub, bytes):
            link = first(sub, 7)
            if isinstance(link, bytes):
                nested = first(link, 1)
                if isinstance(nested, bytes):
                    token = first(nested, 2)
                    if isinstance(token, int):
                        used.add(token)
    return used


def _fresh_token(used: set[int]) -> int:
    while True:
        value = uuid.uuid4().int & 0xFFFFFFFF
        if value and value not in used:
            used.add(value)
            return value


def _refresh_links(metadata: bytes, sub: bytes, used_tokens: set[int]) -> tuple[bytes, bytes]:
    metadata_link = first(metadata, 2)
    content_link = first(sub, 15)
    style_link = first(sub, 7)
    if not all(isinstance(value, bytes) for value in
               (metadata_link, content_link, style_link)):
        raise ValueError("pen record lacks required linked fields")
    assert isinstance(metadata_link, bytes)
    assert isinstance(content_link, bytes)
    assert isinstance(style_link, bytes)
    nested_style = first(style_link, 1)
    if not isinstance(nested_style, bytes):
        raise ValueError("pen record lacks nested style link")
    token = _fresh_token(used_tokens)
    metadata = replace(metadata, 2, replace(metadata_link, 2, token))
    sub = replace(sub, 15, replace(content_link, 2, token))
    nested_style = replace(nested_style, 2, _fresh_token(used_tokens))
    sub = replace(sub, 7, replace(style_link, 1, nested_style))
    return metadata, sub


def _max_sequence(recs: list[bytes]) -> int:
    return max((field.value for rec in recs for field in fields(rec)
                if field.number == 9 and isinstance(field.value, int)), default=0)


def _document_value(recs: list[bytes]) -> int:
    values = {value for rec in recs if isinstance(value := first(rec, 8), int)}
    if len(values) != 1:
        raise ValueError("template page must have one consistent document value")
    return values.pop()


def _recipient_pen(template: Path, source: PenTemplate) -> PenTemplate:
    """Use a working pen wrapper from the destination document when present."""
    if template.resolve() == source.source.resolve():
        return source
    try:
        return find_pen(template)
    except ValueError:
        return source


def _record_pair(metadata: bytes, content: bytes, raw: bytes,
                 color: tuple[float, float, float, float], sequence: int,
                 document_value: int, used: set[bytes],
                 used_tokens: set[int]) -> tuple[bytes, bytes]:
    pen_id = _fresh_id(used)
    metadata = replace(metadata, 1, pen_id)
    metadata = replace(metadata, 8, document_value)
    if first(metadata, 9) is not None:
        metadata = replace(metadata, 9, sequence)
    sub = first(content, 7)
    assert isinstance(sub, bytes)
    sub = replace(sub, 1, pen_id)
    sub = replace(sub, 2, compress(raw))
    sub = replace(sub, 4, _rgba(color))
    metadata, sub = _refresh_links(metadata, sub, used_tokens)
    return metadata, replace(content, 7, sub)


def encode(document: InkDocument, *, template: Path, output: Path,
           pen_source: Path | None = None, canvas_scale: float = 6 / 11,
           page_index: int = 0) -> EncodeResult:
    """Add each internal stroke as one native pen object to a template page."""
    validate(document)
    if output.resolve() in {template.resolve(), (pen_source or template).resolve()}:
        raise ValueError("output must differ from source Goodnotes archives")
    if not 0 < canvas_scale <= 10:
        raise ValueError("canvas_scale must be positive")
    page = document.pages[page_index]
    archive = open_archive(template)
    member = choose_page(archive)
    source_records = records(archive.read(member))
    document_value = _document_value(source_records)
    recs: list[bytes] = []
    used = _existing_ids(source_records)
    used_tokens = _existing_tokens(source_records)
    pen = find_pen(pen_source or template, prefer_straight=True)
    recipient = _recipient_pen(template, pen)
    sequence = _max_sequence(source_records)
    decoded = []
    ids = []
    for stroke in page.strokes:
        if stroke.tool.lower() not in ("pen", "pencil"):
            raise ValueError(f"unsupported native tool {stroke.tool!r}; only pen is encoded")
        raw = transform(pen.geometry, stroke.points, canvas_scale=canvas_scale)
        sequence += 1
        metadata, content = _record_pair(recipient.metadata, recipient.content, raw,
                                         stroke.color, sequence, document_value, used,
                                         used_tokens)
        recs.extend((metadata, content))
        sub = first(content, 7)
        assert isinstance(sub, bytes)
        pen_id, blob = first(sub, 1), first(sub, 2)
        assert isinstance(pen_id, bytes) and isinstance(blob, bytes)
        ids.append(pen_id.decode("ascii"))
        decoded.append(sampled_points(decompress(blob)))
    archive.write(output, {member: pack_records(recs)})
    return EncodeResult(output, member, ids, decoded)


def encode_strokes(strokes: list[Stroke], *, page_width: float, page_height: float,
                   template: Path, output: Path, pen_source: Path | None = None,
                   canvas_scale: float = 6 / 11) -> EncodeResult:
    """Encode any valid internal Stroke collection without an InkSight adapter."""
    document = InkDocument("native-ink", [Page(page_width, page_height,
        "page_points_top_left", strokes)])
    return encode(document, template=template, output=output,
                  pen_source=pen_source, canvas_scale=canvas_scale)


def encode_affine_clone(*, template: Path, pen_source: Path, output: Path,
                        affine: tuple[float, float, float, float, float, float]) -> EncodeResult:
    """Controlled native-template experiment; affine values are canvas-space."""
    if output.resolve() in {template.resolve(), pen_source.resolve()}:
        raise ValueError("output must differ from source Goodnotes archives")
    archive = open_archive(template)
    member = choose_page(archive)
    source_records = records(archive.read(member))
    document_value = _document_value(source_records)
    recs: list[bytes] = []
    used = _existing_ids(source_records)
    used_tokens = _existing_tokens(source_records)
    pen = find_pen(pen_source, prefer_straight=True)
    recipient = _recipient_pen(template, pen)
    raw = pen.geometry if affine == (1, 0, 0, 1, 0, 0) else transform(
        pen.geometry, [StrokePoint(0, 0, 1)], canvas_scale=1, affine=affine)
    sub = first(recipient.content, 7)
    assert isinstance(sub, bytes)
    source_sub = first(pen.content, 7)
    assert isinstance(source_sub, bytes)
    source_color = first(source_sub, 4)
    assert isinstance(source_color, bytes)
    # Preserve the source color bytes, including sparse/default channels.
    seq = _max_sequence(source_records) + 1
    pen_id = _fresh_id(used)
    metadata = replace(recipient.metadata, 1, pen_id)
    metadata = replace(metadata, 8, document_value)
    if first(metadata, 9) is not None:
        metadata = replace(metadata, 9, seq)
    sub = replace(sub, 1, pen_id)
    sub = replace(sub, 4, source_color)
    if affine == (1, 0, 0, 1, 0, 0):
        source_blob = first(source_sub, 2)
        assert isinstance(source_blob, bytes)
        sub = replace(sub, 2, source_blob)
    else:
        sub = replace(sub, 2, compress(raw))
    metadata, sub = _refresh_links(metadata, sub, used_tokens)
    content = replace(recipient.content, 7, sub)
    recs.extend((metadata, content))
    archive.write(output, {member: pack_records(recs)})
    pen_id, blob = first(sub, 1), first(sub, 2)
    assert isinstance(pen_id, bytes) and isinstance(blob, bytes)
    return EncodeResult(output, member, [pen_id.decode("ascii")],
                        [sampled_points(decompress(blob))])
