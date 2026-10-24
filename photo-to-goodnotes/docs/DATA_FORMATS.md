# Internal handwriting schema v1.0

The Python contract lives in `src/inkbridge/core/models.py`; `tests/fixtures/ink_document.json` is an illustrative JSON representation. Adapters will own JSON encoding and validation later.

All page dimensions, `x`, `y`, and `width` use page points (`1 pt = 1/72 inch`). Origin is the top-left of each page, `x` grows right, `y` grows down. Width is rendered stroke diameter, not radius. A pixel-to-point conversion requires a documented DPI or calibrated page transform; never assume image pixels equal points. PDF commonly uses a bottom-left origin, so its y conversion is `page.height - y`. Raw InkSight units and Goodnotes units must be measured at their boundaries.

`color` is RGBA with four floats in `[0, 1]`. `pressure`, if present, is a source-relative value in `[0, 1]`; `timestamp`, if present, is elapsed seconds from the beginning of a stroke. Point order is drawing order. `id` values are unique within a document. `tool` is a source-neutral label such as `pen`; vendor tool codes belong in adapter metadata. `source_metadata` should identify provenance without storing private image bytes. `background_reference` is a path or URI reference, never flattened ink.

Serialization rules (field omission versus null, migration, strict range checks) remain for implementation; the fixture shows intended field names and shape.
