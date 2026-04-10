# Portrait Legacy Kernel

This package is the copy-first migration landing area for the historical
portrait-builder kernel.

Current factual status:

- copied from the accessible old baseline under
  `reference/Tashan-TopicLab/backend/...`
- local assets now live inside this package under `assets/`
- the current migrated first batch is:
  - `prompts.py`
  - `tools.py`
  - `profile_parser.py`
  - profile template
  - helper docs
  - skill markdown files

Migration rule:

- preserve old business logic first
- adapt only imports, asset paths, and storage/session boundaries
- avoid replacing old behavior with newly handwritten logic unless old source
  is truly unavailable
