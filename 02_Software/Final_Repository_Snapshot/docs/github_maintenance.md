# Repository Maintenance Compatibility Note

This former page is retained only so older links remain valid.

- Repository structure and generated-artifact policy:
  [13_PROJECT_TREE.md](13_PROJECT_TREE.md)
- Offline submission checks: [VERSION_INFO.md](../VERSION_INFO.md)
- Protected hybrid experiment record:
  [ORIGINAL_DEPTH_LUT_EXPERIMENT_2026-07-25.md](ORIGINAL_DEPTH_LUT_EXPERIMENT_2026-07-25.md)

Treat `Original/` as read-only, keep datasets and trained weights outside Git, and run
`python scripts/verify_submission.py` before packaging.
