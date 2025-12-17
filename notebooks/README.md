# Notebooks

This folder holds notebooks for collecting OpenReview papers and reviews from ICLR and NeurIPS.

## Main notebook
- `note_review_collect.ipynb` is the cleaned workflow that pulls papers/reviews using OpenReview API v2 with a v1 fallback; it targets ICLR 2016–2025 and NeurIPS 2019, 2021–2025 (note: ICLR 2016 and NeurIPS 2019 are treated as workshops).
- Requires Python 3 with `openreview`, `openreview.api`, `pandas`, and standard libs (`json`, `os`, `shutil`); `requests` and `markitdown` are only used in the optional `get_pdf_markdown` helper (labeled “do not run” locally in the notebook).
- Helper functions: `convert_2_json`/`save_json` for serialization, `getAttr` for nested field extraction, `paperCleaner` to standardize decisions/reviews/pdf URLs/revision flags, and `print_results` to show output sizes.
- Playground cells let you fetch invitation URLs or test pull a single venue before running the full sweep.

## Final run logic
- The final cell loops through `venue_invitations_url`, downloads notes with `details="directReplies,revisions"`, retries with API v1 if empty, and writes cleaned records to `notebook out/{VENUE}.jsonl` (the folder is recreated each run).
- Each JSONL line includes `id`, `title`, `authors`, `created_date`, `pdf_url` (prefixed with `https://openreview.net` when present), `original_paper_id`, `has_revisions`, `decision`, and `reviews` (list of `{date, review}` with meta-reviews filtered when needed).
- Sample saves like `single_paper.json`/`playground_*` can be produced from the testing cells to inspect raw structures.

## File naming
- `.ipynb` files beginning with `scrapnote_` are messy scratch notes; use `note_review_collect.ipynb` for the readable workflow.

## Cautions
- `get_pdf_markdown` downloads PDFs and converts them to text; the notebook flags it as a safety hazard to avoid running locally.
- The final cell deletes and recreates `notebook out`, so copy any previous outputs before rerunning.
