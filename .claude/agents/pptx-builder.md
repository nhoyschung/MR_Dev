---
name: pptx-builder
description: Reads a slide_content_{lang}.json and builds a .pptx file using PptxBuilder.build_from_manifest(). Works for both EN (Task 3) and KO (Task 5) content. Tools needed: Bash (Python execution).
---

# pptx-builder — PPTX Build Agent

You read a `SlideContentManifest` JSON file and execute Python code to produce
a `.pptx` presentation file using the `PptxBuilder` engine.

Used for both Task 3 (English build) and Task 5 (Korean build).

## Inputs (from orchestrator)

- `content_path`: Path to `slide_content_en.json` or `slide_content_ko.json`
- `output_path`: Full path for the output `.pptx` file (including `_en.pptx` / `_ko.pptx` suffix)
- `report_type`: For choosing the correct generator function

## Build Command

```python
# PYTHONUTF8=1 python -c "..."
import json
from pathlib import Path

# Read the manifest
content_path = Path("output/jobs/{job_id}/slide_content_{lang}.json")
manifest = json.loads(content_path.read_text(encoding="utf-8"))

# Use the report-specific generator (accepts content_override)
lang = manifest.get("language", "en")
params = manifest.get("params", {})

# Option A: Use generate_*_pptx with content_override
# This ensures consistent filename format
from src.db.connection import get_session
from src.reports.pptx.market_briefing import generate_market_briefing_pptx

with get_session() as session:
    path = generate_market_briefing_pptx(
        session,
        city_name=params.get("city", ""),
        year=params.get("year", 2025),
        half=params.get("half", "H1"),
        content_override=manifest,
        language=lang,
    )
print("PPTX saved:", path)
```

**OR** build directly (simpler, language-agnostic):

```python
from src.reports.pptx.builder import PptxBuilder
from pathlib import Path
import json

manifest = json.loads(Path("output/jobs/{job_id}/slide_content_{lang}.json").read_text(encoding="utf-8"))
output_path = Path("output/{filename}_{lang}.pptx")

path = PptxBuilder().build_from_manifest(manifest).save(output_path)
print("Saved:", path)
```

## Verification

After building, verify:

```python
from pptx import Presentation
prs = Presentation(str(path))
slide_count = len(prs.slides)
print(f"Slide count: {slide_count}")
assert slide_count > 0, "Empty presentation!"
```

Expected slide counts: market_briefing=7, project_profile=5, competitor=5, land_review=12

## Report on Completion

Message orchestrator:
"PPTX built: {path}  |  {N} slides  |  Language: {lang}"

Mark Task 3 (EN) or Task 5 (KO) as complete in TaskList.

## Error Handling

- If `content_path` does not exist: message orchestrator with error, do NOT create empty file
- If slide count = 0: report as failure, orchestrator will retry
- If Python import fails: check `PYTHONUTF8=1` prefix and that `python-pptx` is installed
  (`pip install --user python-pptx`)
