import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PIL import Image

from inkbridge.core.exceptions import InkBridgeError
from inkbridge.inksight.adapter import normalize_prediction
from inkbridge.inksight.inkml_parser import parse_inkml, parse_tokens
from inkbridge.preprocessing.image_loader import load_image, pad_for_inksight
from inkbridge.rendering.reference import render, render_svg
from inkbridge.strokes.validation import save_json, validate


def test_inkml_traces_keep_order(tmp_path):
    path = tmp_path / "sample.inkml"
    path.write_text('<ink xmlns="http://www.w3.org/2003/InkML">'
                    '<trace>1,2 3,4</trace><trace>8,7 6,5</trace></ink>')
    assert parse_inkml(path) == [[(1, 2), (3, 4)], [(8, 7), (6, 5)]]


@pytest.mark.parametrize("contents", ["<ink>", "<ink/>",
    '<ink xmlns="http://www.w3.org/2003/InkML"><trace>1,no</trace></ink>'])
def test_malformed_inkml(tmp_path, contents):
    path = tmp_path / "bad.inkml"
    path.write_text(contents)
    with pytest.raises(InkBridgeError):
        parse_inkml(path)


def test_tokens_preserve_stroke_boundaries():
    assert parse_tokens("<ink_token_1><ink_token_227><ink_token_3><ink_token_229>"
                        "<ink_token_450><ink_token_8><ink_token_232>") == [
                            [(1, 2), (3, 4)], [(8, 7)]]
    with pytest.raises(InkBridgeError):
        parse_tokens("plain text")
    with pytest.raises(InkBridgeError):
        parse_tokens("<ink_token_450>")


def test_transform_and_json_and_render(tmp_path):
    source = Image.new("RGB", (400, 200), "white")
    padded, transform = pad_for_inksight(source)
    assert padded.size == (224, 224)
    assert transform.to_source(112, 112) == pytest.approx((200, 100))
    raw = {"image_width": 400, "image_height": 200,
           "strokes": [[[0, 0], [400, 200]], [[200, 100]]]}
    doc = normalize_prediction(raw, Path("example.png"), dpi=144)
    validate(doc)
    assert doc.pages[0].width == 200
    assert [(p.x, p.y) for p in doc.pages[0].strokes[0].points] == [(0, 0), (200, 100)]
    assert doc.pages[0].strokes[1].points[0].pressure is None
    saved = json.loads(save_json(doc, tmp_path / "strokes.json").read_text())
    assert saved["schema_version"] == "1.0"
    assert len(saved["pages"][0]["strokes"]) == 2
    png = render(doc, page_index=0, output=tmp_path / "preview.png")
    assert Image.open(png).getpixel((200, 100)) != (255, 255, 255)
    svg = render_svg(doc, page_index=0, output=tmp_path / "preview.svg")
    assert len(ET.parse(svg).getroot()) == 3


def test_bad_image_and_model_outputs(tmp_path):
    with pytest.raises(InkBridgeError):
        load_image(tmp_path / "missing.jpg")
    for raw in ({"image_width": 10, "image_height": 10, "strokes": []},
                {"image_width": 10, "image_height": 10, "strokes": [[]]},
                {"image_width": 10, "image_height": 10, "strokes": [[["nan", 1]]]}):
        with pytest.raises(InkBridgeError):
            normalize_prediction(raw, Path("photo.jpg"), dpi=300)
