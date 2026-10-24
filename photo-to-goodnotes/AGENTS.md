# Working agreements

- This directory is an independent project. Do not edit the parent `goodparse` project or any future `t/` files while working here.
- Keep `InkDocument` independent of InkSight and Goodnotes. Change the schema deliberately and update its JSON fixture and `docs/DATA_FORMATS.md` together.
- Replace interface stubs one component at a time. Do not silently claim that a `.goodnotes` file is editable without an import, reopen, move/delete, and partial erase check in Goodnotes.
- Treat Goodnotes field notes as observations, not a stable specification. Preserve unknown archive and protobuf records.
- Keep InkSight dependencies in its own environment. Keep training dependencies optional.
- Do not vendor `goodparse` code into `src/inkbridge`; review its upstream GPL-3.0 license before reuse.
- Never commit photographs, weights, generated documents, or user `.env` values.
