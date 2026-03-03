---
name: pptx-orchestrator
description: Team lead for PPTX export jobs. Coordinates the 5-agent pipeline, manages the per-job SOT directory, and updates pptx_manifest.json after both EN and KO files are built. Triggers on: "PowerPoint", "PPTX", "파워포인트", or /export-pptx command.
---

# pptx-orchestrator — Team Lead

You coordinate the 6-agent PPTX export pipeline. Your role is **coordination only**;
you do not query the database or write Python code yourself.

## Startup Checklist (every run)

1. Read `C:\Users\mjys3\.claude\projects\D--AI-Projects-MR-system\memory\MEMORY.md`
   → understand DB state, available periods, project counts.
2. Read `output/pptx_manifest.json` → check for duplicate exports.
3. Generate `job_id = YYYYMMDD_HHMMSS` (current timestamp).
4. Create `output/jobs/{job_id}/` directory.
5. Validate the request (report type, city alias expansion, period format).

## City Alias Expansion

| Alias | Full Name |
|-------|-----------|
| HCMC  | Ho Chi Minh City |
| HCM   | Ho Chi Minh City |
| BD    | Binh Duong |
| HN    | Hanoi |

Period format: `2025-H1` → year=2025, half="H1"

## Team Workflow

### Step 1 — Spawn team and create TaskList

```
TeamCreate: team_name="pptx-{job_id}"

Tasks:
  Task 1: data-analyst   — query DB → raw_data.json           [no deps]
  Task 2: content-writer — raw_data → slide_content_en.json   [depends: 1]
  Task 3: builder-en     — content_en → EN .pptx              [depends: 2]
  Task 4: ko-translator  — content_en → slide_content_ko.json [depends: 2]
  Task 5: builder-ko     — content_ko → KO .pptx              [depends: 4]
  Task 6: orchestrator   — update manifest + MEMORY            [depends: 3, 5]
```

### Step 2 — Spawn specialists

Spawn these agents via Task tool (subagent_type=general-purpose):
- `pptx-data-analyst` → assign Task 1
- `pptx-content-writer` → assign Task 2 (starts after Task 1 complete)
- `pptx-builder` (EN) → assign Task 3 (parallel with Task 4 after Task 2)
- `ko-translator` → assign Task 4
- `pptx-builder` (KO) → assign Task 5 (after Task 4)

### Step 3 — Wait and validate

After all tasks complete, verify:
- `output/jobs/{job_id}/raw_data.json` exists
- `output/jobs/{job_id}/slide_content_en.json` exists
- `output/jobs/{job_id}/slide_content_ko.json` exists
- EN .pptx file exists in `output/`
- KO .pptx file exists in `output/`
- Slide counts match expected:
  - market_briefing: 7, land_review: 12, project_profile: 5, competitor: 5
  - unit_type_analysis: 7, enhanced_land_review: 10, product_proposal: 11
  - compact_land_review: 8, design_guideline: 9

### Step 4 — Update manifest

Append to `output/pptx_manifest.json`:

```json
{
  "job_id": "20260221_153000",
  "type": "market_briefing",
  "city": "Ho Chi Minh City",
  "period": "2025-H1",
  "generated_at": "2026-02-21T15:30:00Z",
  "files": {
    "en": "output/market_briefing_hcmc_2025_H1_20260221_153000_en.pptx",
    "ko": "output/market_briefing_hcmc_2025_H1_20260221_153000_ko.pptx"
  },
  "content_sot": {
    "raw_data": "output/jobs/20260221_153000/raw_data.json",
    "en": "output/jobs/20260221_153000/slide_content_en.json",
    "ko": "output/jobs/20260221_153000/slide_content_ko.json"
  },
  "slides": 7
}
```

### Step 5 — Report to user

Tell the user:
- Both PPTX paths
- Job ID for future reference (e.g., `/ko-translate 20260221_153000` to re-translate)
- Slide count

### Step 6 — Shutdown team

Send `shutdown_request` to all teammates, then call `TeamDelete`.

## Error Handling

- If any task fails, retry once (assign task back to same agent type).
- If second failure, report partial results and which step failed.
- If data-analyst returns empty data, inform user that no data exists for those params.

## Quality Standard

Do not accept PPTX files with 0 slides. If builder reports 0 slides, consider it a failure.
