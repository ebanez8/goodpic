# Experimental Goodnotes format notes

These are observations from sample files and reverse engineering, **not a guaranteed specification**. A `.goodnotes` file is a ZIP archive with page records under `notes/<UUID>`. Page content records contain field `#7`; a stroke record has field `#2` compressed geometry, field `#4` RGBA color, and pen-related field `#21` in observed examples. Geometry uses Apple-framed LZ4 (`bv41` blocks and `bv4$` terminator). Records are protobuf wire data, often length-delimited.

Vector line geometry and freehand pen geometry are different. Extracted `(x, y, width)` triples describe only part of a pen's path; freehand records may contain additional curve/control points, flags, style templates, and trailing data. Editing only triples while retaining inconsistent companion data can produce distorted renderings. The reported injected letter A imported and remained movable/deletable after reopening, but rendered incorrectly. Partial erasing is unverified.

Future encoder work must preserve unknown ZIP members, protobuf fields, order-sensitive metadata where necessary, and template data. Compare controlled native strokes against inserted strokes before interpreting any byte sequence as a stable field. The brief names `t/output/experiment.py` as the baseline, but `t/` is absent in this checkout. The root `goodparse` source and `samples/` can inform read-only investigation; they are outside this package.

The referenced upstream `goodparse` repository identifies GPL-3.0. Do not copy its source into InkBridge or assume proprietary distribution compatibility. This checkout's `pyproject.toml` currently labels the parent package MIT, creating a licensing discrepancy that requires review before reuse.
