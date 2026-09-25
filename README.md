# Greenhouse Export Tool

One-command export of all candidates, applications, and resumes from a Greenhouse ATS instance.

## Quick Start

```bash
bash greenhouse_export.sh
```

The script guides you through setup on first run (saves credentials for next time), then exports:
- **export_candidates.csv** — all candidate + application data
- **resumes/** — resumes organized by department → role

## What's Included

- `greenhouse_export.sh` — Interactive setup wizard + orchestration
- `greenhouse_export.py` — Core export logic (candidates, applications, jobs, resumes)
- `.env.template` — Credential template
- `QUICK_START.txt` — Quick reference
- `GREENHOUSE_EXPORT_README.md` — Detailed documentation

## Requirements

- Python 3.7+
- Bash
- Greenhouse v3 OAuth2 API credentials

## How It Works

1. **First run:** Interactive wizard prompts for 3 credentials (saves to `.env`)
2. **Subsequent runs:** Reads saved credentials, no prompts
3. **Export:** Fetches all candidates/applications/jobs via v3 API, downloads resumes, creates CSV

## Credentials Needed

From your Greenhouse account:
- **v3 CLIENT ID** — Settings → API Credentials → OAuth2 Provider
- **v3 CLIENT SECRET** — Same location
- **USER ID** — Your profile or Settings → Users

## Output

```
greenhouse_export/
├── export_candidates.csv          # Master spreadsheet
└── resumes/
    ├── Engineering/
    │   ├── Senior Engineer/
    │   │   └── 12345_jane_doe.pdf
    │   └── Junior Engineer/
    │       └── 12346_john_smith.pdf
    └── Sales/
        └── Account Executive/
            └── 12347_alice_johnson.pdf
```

CSV columns: `candidate_id`, `first_name`, `last_name`, `email`, `phone`, `job_id`, `job_name`, `department`, `application_status`, `stage`, `created_at`, `updated_at`, `tags`, `resumes_downloaded`

## Crash Recovery & Progress Tracking

**Automatic Checkpointing:**
- Saves progress to `export_progress.json` after each resume
- If interrupted (crash, network, manual stop), just run again
- Automatically skips already-downloaded resumes

**3-Level Progress Display:**
1. **Per-role completion** — `✓ Engineering → Senior Engineer: 5 resumes`
2. **Per-department summary** — Shows total per department at end
3. **Overall progress** — Percentage during processing (every 100 applications)

**Logging:**
- Console output with timestamps
- Full log saved to `export_progress.log` for later review
- Both show same info (console for live monitoring, log for records)

## Notes

- Fully automated (no UI, no external services)
- Handles large datasets (1000+ candidates)
- Resumes pre-signed URLs expire in ~7 days
- Resumable on crash — keeps checkpoint file

## License

MIT
