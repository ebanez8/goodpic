"""Local structural and geometry checks; no app-compatibility claim."""

import struct
import zipfile
from pathlib import Path

import pytest

from inkbridge.core.models import StrokePoint
from inkbridge.goodnotes.archive import open_archive
from inkbridge.goodnotes.compression import compress, decompress
from inkbridge.goodnotes.encoder import encode, encode_affine_clone, encode_strokes
from inkbridge.goodnotes.geometry import layout, resample, sampled_points, transform
from inkbridge.goodnotes.protobuf import encode_field, fields, first, pack_records, records, replace
from inkbridge.goodnotes.reader import find_pen
from inkbridge.rendering.reference import render
from inkbridge.strokes.validation import load_json

ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_TEMPLATE = ROOT.parent / "samples" / "test.goodnotes"
PEN_SOURCE = ROOT.parent / "samples" / "Test5.goodnotes"
LOOP_SOURCE = ROOT.parent / "samples" / "Test4.goodnotes"
JSON_FIXTURE = ROOT / "tests" / "fixtures" / "ink_document.json"


def test_wire_unknown_fields_and_records():
    original = encode_field(1, 2, b"old") + encode_field(999, 2, b"unknown")
    edited = replace(original, 1, b"new")
    assert first(edited, 1) == b"new"
    assert fields(edited)[1].raw == fields(original)[1].raw
    assert records(pack_records([original, edited])) == [original, edited]
    with pytest.raises(ValueError):
        records(b"\x05bad")


@pytest.mark.parametrize("size", [1, 14, 15, 256, 65537])
def test_apple_lz4_roundtrip(size):
    raw = bytes(i % 251 for i in range(size))
    assert decompress(compress(raw)) == raw
    assert decompress(b"bv4-" + struct.pack("<I", size) + raw + b"bv4$") == raw


def test_apple_lz4_compresses_repeated_bytes():
    raw = b"Goodnotes ink geometry" * 200
    blob = compress(raw)
    assert blob.startswith(b"bv41")
    assert len(blob) < len(raw)
    assert decompress(blob) == raw


def test_real_pen_layout_and_companion_transforms():
    pen = find_pen(LOOP_SOURCE)
    info = layout(pen.geometry)
    assert info.count == 52
    assert (info.outline_end - info.outline) // 8 == 195
    original = sampled_points(pen.geometry)
    translated = transform(pen.geometry, [], canvas_scale=1,
                           affine=(1, 0, 0, 1, 30, 20))
    moved = sampled_points(translated)
    assert moved[0][0] == pytest.approx(original[0][0] + 30)
    assert moved[0][1] == pytest.approx(original[0][1] + 20)
    x, y = struct.unpack_from("<ff", pen.geometry, info.outline)
    nx, ny = struct.unpack_from("<ff", translated, info.outline)
    assert (nx, ny) == pytest.approx((x + 30, y + 20))
    scaled = transform(pen.geometry, [], canvas_scale=1,
                       affine=(1.25, 0, 0, 1.25, 0, 0))
    assert sampled_points(scaled)[0] == pytest.approx(tuple(v * 1.25 for v in original[0]))


def test_native_dot_has_tiny_nonzero_path():
    points = resample([StrokePoint(30, 40, 1.2)], 52)
    assert len(points) == 52
    assert points[0].x < 30 < points[-1].x
    assert points[-1].x - points[0].x < 0.1


def test_outline_separator_is_not_transformed():
    raw = find_pen(PEN_SOURCE, prefer_straight=True).geometry
    info = layout(raw)
    target = [StrokePoint(80, 160, 1.6), StrokePoint(120, 80, 1.6),
              StrokePoint(160, 160, 1.6)]
    changed = transform(raw, target, canvas_scale=6 / 11)
    sentinel_offsets = [offset for offset in range(info.outline, info.outline_end, 8)
                        if (lambda x, y: x == 0 and 0 < abs(y) < 1e-30)(
                            *struct.unpack_from("<ff", raw, offset))]
    assert sentinel_offsets
    assert all(changed[offset:offset + 8] == raw[offset:offset + 8]
               for offset in sentinel_offsets)
    outline = [struct.unpack_from("<ff", changed, offset)
               for offset in range(info.outline, info.outline_end, 8)
               if offset not in sentinel_offsets]
    assert all(70 < x * 6 / 11 < 170 and 70 < y * 6 / 11 < 170 for x, y in outline)


def test_affine_translation_preserves_non_geometry_bytes():
    raw = find_pen(PEN_SOURCE, prefer_straight=True).geometry
    info = layout(raw)
    changed = transform(raw, [], canvas_scale=1, affine=(1, 0, 0, 1, 30, 20))
    mutable = bytearray(len(raw))
    for start, end in ((info.anchor, info.anchor + 12),
                       (info.points, info.points + 12 * info.count),
                       (info.controls, info.controls + 20 * info.count)):
        mutable[start:end] = b"\x01" * (end - start)
    for offset in range(info.outline, info.outline_end, 8):
        first_word, second_word = struct.unpack_from("<II", raw, offset)
        if first_word == 0 and 0 < second_word < 1_000_000:
            continue
        mutable[offset:offset + 8] = b"\x01" * 8
        x, y = struct.unpack_from("<ff", raw, offset)
        nx, ny = struct.unpack_from("<ff", changed, offset)
        assert (nx, ny) == pytest.approx((x + 30, y + 20), abs=1e-4)
    for i in range(info.count):
        start = info.controls + 20 * i
        x, y, width, tangent_x, tangent_y = struct.unpack_from("<fffff", raw, start)
        nx, ny, nwidth, ntx, nty = struct.unpack_from("<fffff", changed, start)
        assert (nx, ny, nwidth, ntx, nty) == pytest.approx(
            (x + 30, y + 20, width, tangent_x, tangent_y), abs=1e-4)
    assert all(a == b for a, b, may_change in zip(raw, changed, mutable, strict=True)
               if not may_change)


def test_end_to_end_archive_and_metadata(tmp_path):
    document = load_json(JSON_FIXTURE)
    result = encode(document, template=DOCUMENT_TEMPLATE, pen_source=PEN_SOURCE,
                    output=tmp_path / "generated.goodnotes")
    assert result.path.exists()
    assert len(result.stroke_ids) == 1
    assert len(set(result.stroke_ids)) == 1
    with zipfile.ZipFile(result.path) as z:
        assert z.testzip() is None
    before = open_archive(DOCUMENT_TEMPLATE)
    after = open_archive(result.path)
    assert before.names() == after.names()
    assert all(before.read(name) == after.read(name) for name in before.names()
               if name != result.page_member)
    old_recs = records(before.read(result.page_member))
    new_recs = records(after.read(result.page_member))
    assert len(old_recs) == 4
    assert len(new_recs) == 2
    inserted = first(new_recs[-1], 7)
    assert isinstance(inserted, bytes)
    assert first(new_recs[0], 1) == first(inserted, 1)
    assert first(new_recs[0], 8) == first(old_recs[0], 8)
    recipient = find_pen(DOCUMENT_TEMPLATE)
    assert first(first(new_recs[0], 2), 1) == first(first(recipient.metadata, 2), 1)
    assert first(new_recs[0], 2) == first(inserted, 15)
    assert first(new_recs[0], 2) != first(recipient.metadata, 2)
    assert first(inserted, 7) != first(first(recipient.content, 7), 7)
    assert first(inserted, 21) == 24
    assert first(inserted, 1).decode() == result.stroke_ids[0]
    raw = decompress(first(inserted, 2))
    points = sampled_points(raw)
    assert points[0][:2] == pytest.approx((72 * 11 / 6, 72 * 11 / 6))
    assert points[-1][:2] == pytest.approx((80 * 11 / 6, 82 * 11 / 6))
    assert points[0][2] == pytest.approx(1.2 * 11 / 12)
    assert points[-1][2] == pytest.approx(1.1 * 11 / 12)
    intended = resample(document.pages[0].strokes[0].points, len(points))
    for actual, target in zip(points, intended, strict=True):
        assert actual == pytest.approx((target.x * 11 / 6, target.y * 11 / 6,
                                        target.width * 11 / 12), abs=1e-4)
    assert first(inserted, 6) == first(first(find_pen(PEN_SOURCE,
        prefer_straight=True).content, 7), 6)
    preview = render(document, page_index=0, output=tmp_path / "reference.png")
    assert preview.exists()


def test_clone_preserves_raw_geometry(tmp_path):
    result = encode_affine_clone(template=DOCUMENT_TEMPLATE, pen_source=PEN_SOURCE,
                                 output=tmp_path / "clone.goodnotes",
                                 affine=(1, 0, 0, 1, 0, 0))
    archive = open_archive(result.path)
    written = records(archive.read(result.page_member))
    sub = first(written[-1], 7)
    assert first(written[0], 1) == first(sub, 1)
    template = open_archive(DOCUMENT_TEMPLATE)
    assert first(written[0], 8) == first(records(template.read(result.page_member))[0], 8)
    assert first(written[0], 2) == first(sub, 15)
    assert first(written[0], 2) != first(find_pen(DOCUMENT_TEMPLATE).metadata, 2)
    assert decompress(first(sub, 2)) == find_pen(PEN_SOURCE,
        prefer_straight=True).geometry
    source_sub = first(find_pen(PEN_SOURCE, prefer_straight=True).content, 7)
    assert first(sub, 2) == first(source_sub, 2)


def test_saved_inksight_word_keeps_stroke_order_and_unique_uuids(tmp_path):
    document = load_json(ROOT / "tests" / "fixtures" / "inksight_word.json")
    result = encode(document, template=DOCUMENT_TEMPLATE, pen_source=PEN_SOURCE,
                    output=tmp_path / "word.goodnotes")
    assert len(result.stroke_ids) == len(document.pages[0].strokes) == 7
    assert len(set(result.stroke_ids)) == 7
    written = records(open_archive(result.path).read(result.page_member))
    metadata_tokens = [first(first(written[i], 2), 2) for i in range(0, len(written), 2)]
    style_tokens = [first(first(first(first(written[i + 1], 7), 7), 1), 2)
                    for i in range(0, len(written), 2)]
    assert len(set(metadata_tokens)) == len(set(style_tokens)) == 7
    assert all(first(written[i], 2) == first(first(written[i + 1], 7), 15)
               for i in range(0, len(written), 2))
    for native, source in zip(result.decoded_points, document.pages[0].strokes, strict=True):
        assert native[0][:2] == pytest.approx((source.points[0].x * 11 / 6,
                                              source.points[0].y * 11 / 6), abs=0.1)


def test_invalid_pen_template_rejected(tmp_path):
    with zipfile.ZipFile(tmp_path / "empty.goodnotes", "w") as archive:
        archive.writestr("notes/EMPTY", b"")
    with pytest.raises(ValueError, match="genuine freehand"):
        find_pen(tmp_path / "empty.goodnotes")


def test_source_archive_cannot_be_overwritten():
    document = load_json(JSON_FIXTURE)
    with pytest.raises(ValueError, match="output must differ"):
        encode(document, template=DOCUMENT_TEMPLATE, pen_source=PEN_SOURCE,
               output=DOCUMENT_TEMPLATE)


def test_encoder_accepts_plain_stroke_collection(tmp_path):
    document = load_json(JSON_FIXTURE)
    result = encode_strokes(document.pages[0].strokes,
        page_width=document.pages[0].width, page_height=document.pages[0].height,
        template=DOCUMENT_TEMPLATE, pen_source=PEN_SOURCE,
        output=tmp_path / "plain.goodnotes")
    assert len(result.stroke_ids) == 1
