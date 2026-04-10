# Scientist Dossiers

This directory stores the working archive for the 120-person deceased-scientist candidate pool.

## Structure

- `archive/`: one comparable dossier per scientist
- `research/<slug>/`: working notes and evidence buckets for that scientist
- `_template.md`: local pointer template for fast copying inside this directory
- `INDEX.csv`: machine-readable roster and status table

## Current Status

- Scope: 120 deceased scientists
- Current phase: public-only corpus bootstrap completed for all 120 scientists; dossier archive and research buckets are now linked to per-person corpus workspaces
- Goal: continue deep reading, manual correction, and shrink toward 20-30 strong anchor figures
- Reviewed stronger-anchor batch: 20 people

## Status Meaning

- `seeded`: dossier and research buckets created, with initial facts from the candidate pool
- `in_progress`: evidence collection has begun beyond the seed layer
- `reviewed`: dossier has enough evidence for anchor-fit discussion
- `strong_anchor`: reviewed and retained in the stronger anchor subset

## Corpus Status

- `INDEX.csv` now also carries `corpus_status`, `corpus_root`, and `package_root`.
- `corpus_status=corpus_packaged` means the person now has a public-only corpus workspace under `data/scientist-corpora/<slug>/` plus an AI-ready package.
- The legacy `status` column is still kept for anchor-review progress (`seeded` / `reviewed` / `strong_anchor`) instead of being overloaded with corpus lifecycle state.

## Notes

- This folder is not a gallery of biographies; it is a comparable anchor archive for the portrait system.
- Facts, inference, and unknowns should remain separated.
- Do not flatten contradictions just to make a cleaner story.
