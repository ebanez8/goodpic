# Roadmap

1. Verify historical experiments and obtain a known-good template archive.
2. Confirm InkSight inference output and implement isolated worker plus schema conversion. Phase 1 implementation complete; see [InkSight](INKSIGHT.md) for verified run status and limitations.
3. Characterize genuine freehand geometry: measured vA sampled path, outline pairs, control records, and flags; semantics of some fields remain open.
4. Implement archive handling and native pen insertion: local implementation and structural tests complete.
5. Validate six generated documents in Goodnotes: import, PDF export, reopen, move/delete, and partial erase are pending user app testing.
6. Reference render, manual actual-render intake, alignment, metrics, and reports: local implementation complete.
7. Candidate grid and ranking: implemented; correction requires real Goodnotes exports. Learned correction remains optional and out of scope for Phase 2.

Each milestone should be separately testable. Visual fidelity alone does not establish editability.
