# Architecture

`preprocessing` prepares photos; the isolated InkSight worker predicts trajectories; `inksight.adapter` converts its native output into `InkDocument`; `strokes` normalizes and validates; `goodnotes` will encode an existing template archive; `rendering` accepts both a local target preview and a human-supplied Goodnotes export; `evaluation` measures differences; `optimization` records candidates and proposes changes. `learning` is reserved for optional later correction training. `pipeline` composes these boundaries.

The central contract is `src/inkbridge/core/models.py`. Modules may depend on it but it has no dependency on vendor formats. No stage currently performs conversion. Actual Goodnotes rendering requires a manual application step until a renderer adapter exists.

Errors crossing adapters should become `InkBridgeError` subclasses with input paths and context, without hiding source archives or partial outputs. Unknown Goodnotes records must round-trip unchanged. See [roadmap](ROADMAP.md).
