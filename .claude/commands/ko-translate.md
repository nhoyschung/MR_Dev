---
name: ko-translate
description: Re-translate an existing English slide_content_en.json to Korean and rebuild the KO .pptx. Use after editing EN content, or to update terminology. Does NOT re-query the database.
---

# /ko-translate — Korean Translation

Re-translates an existing English content file to Korean and builds a new KO `.pptx`.
Useful for:
- Updating the Korean translation after editing English content
- Changing terminology preferences
- Fixing specific translation issues without full re-export

## Usage

```
/ko-translate {job_id}
/ko-translate {path/to/slide_content_en.json}
```

## Examples

```
/ko-translate 20260221_153000
/ko-translate output/jobs/20260221_153000/slide_content_en.json
```

## What Happens

1. Locate `output/jobs/{job_id}/slide_content_en.json`
2. Spawn `ko-translator` agent → produces new `slide_content_ko.json`
3. Spawn `pptx-builder` agent → produces new KO `.pptx` with new timestamp
4. Update `output/pptx_manifest.json` with new KO file path

## Output

- `output/jobs/{job_id}/slide_content_ko.json` — updated Korean content
- `output/{type}_{params}_{new_timestamp}_ko.pptx` — new Korean PPTX

The English file and EN `.pptx` are **not modified**.

## Note on Job IDs

Job IDs are listed in `output/pptx_manifest.json`. Each export has a unique
`job_id` in `YYYYMMDD_HHMMSS` format.

## Implementation

1. Parse the job_id or path argument
2. Verify `slide_content_en.json` exists
3. Spawn `ko-translator` agent (Task tool, subagent_type=general-purpose,
   agent file: `.claude/agents/ko-translator.md`)
4. After ko-translator completes, spawn `pptx-builder` agent for KO build
5. Update manifest entry (add/update `files.ko` key)
6. Report new KO PPTX path to user
