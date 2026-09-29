# Greenhouse Export Tool

One-command export of all candidates, applications, and resumes from your Greenhouse ATS.

**No Claude account required.** Runs locally or in Claude Code.

## Quick Start

You have two options:

### Option 1: Run Locally (macOS / Linux)
```bash
bash greenhouse_export.sh
```

### Option 2: Run in Claude Code (Easiest for non-technical users)
1. Download/extract the ZIP
2. Upload to Claude Code
3. Ask Claude: "Run the greenhouse export"
4. Claude runs it and shows results

---

**What happens (both options):**
1. On first run: Interactive wizard asks for 3 Greenhouse credentials (saved, one time only)
2. Subsequent runs: Uses saved credentials, no prompts
3. Script automatically:
   - Fetches all candidate + application + job data from Greenhouse API
   - Downloads resumes in parallel (8 at a time)
   - Organizes by department → role
   - Generates CSV with resume status

**Time to completion:** 1-2 hours for 1000+ candidates (parallel downloads)

## What's Included

- `greenhouse_export.sh` — Interactive setup wizard (one-time) + main script
- `greenhouse_export.py` — Core export logic
- `.env.template` — Where credentials get saved (auto-created)
- `QUICK_START.txt` — Quick reference
- `GREENHOUSE_EXPORT_README.md` — Original detailed docs

## Requirements

**To run locally:**
- Python 3.7+ (macOS/Linux have this by default)
- Bash (included with macOS/Linux)
- Greenhouse v3 OAuth2 API credentials

**To run in Claude Code:**
- Greenhouse v3 OAuth2 API credentials
- Internet access
- That's it — Claude handles the rest

**Credentials needed:**
Get from your Greenhouse account settings (see below). You'll enter them once, then never again.

## How It Works

**First Run (Setup):**
```
bash greenhouse_export.sh
→ Wizard prompts for 3 credentials
→ Credentials saved to .env (never ask again)
→ Export starts
```

**Subsequent Runs:**
```
bash greenhouse_export.sh
→ Loads saved credentials from .env
→ Export starts immediately (no prompts)
```

**Export Process:**
1. Fetches all candidates from Greenhouse API
2. Fetches all applications and jobs
3. **Parallel downloads 8 resumes at a time** (automatic retry on network failures)
4. Writes CSV with resume status (`pending` → `yes`/`failed`)
5. If interrupted: run again to resume from checkpoint

## Credentials Needed

Get these from your Greenhouse account (Settings → API Credentials):

- **v3 Client ID** — Under "OAuth2 Provider"
- **v3 Client Secret** — Under "OAuth2 Provider"
- **User ID** — Click your name/avatar → Profile, or Settings → Users (look for your numeric ID)

Takes 2 minutes to find. You'll enter them once, then never again.

## Output Files

```
greenhouse_export/                    ← Main output folder
├── export_candidates.csv             ← Master spreadsheet with all data
├── download_failures.csv             ← Any failed resumes (if any)
├── export_progress.log               ← Detailed log with timestamps
├── export_progress.json              ← Resume checkpoint (internal use)
└── resumes/                          ← Organized by department → role
    ├── Engineering/
    │   ├── Senior Engineer/
    │   │   ├── 12345_jane_doe_att-456.pdf
    │   │   └── 12346_john_smith_att-789.pdf
    │   └── Junior Engineer/
    │       └── 12347_alice_johnson_att-123.pdf
    └── Sales/
        └── Account Executive/
            └── 12348_bob_jones_att-234.pdf

greenhouse_export_partial_run/       ← Temporary folder (delete after done)
└── resumes/                          ← In-progress downloads while running
```

## CSV Columns Explained

| Column | What It Is |
|--------|-----------|
| `candidate_id`, `first_name`, `last_name`, `email`, `phone` | Candidate contact info |
| `job_id`, `job_name`, `department` | Role they applied for |
| `application_status` | `in_process`, `rejected`, `hired` |
| `stage` | Current stage in pipeline (e.g., "Screening", "Interview") |
| `created_at`, `updated_at` | Application dates |
| `tags` | Any tags from Greenhouse |
| `resume_files` | Where resume will be saved (path to file on disk) |
| `resumes_downloaded` | Status: `pending` (waiting) → `yes` (success) / `failed` (error) |

## Features

### Performance
- **8 parallel workers** download resumes simultaneously (vs. 1 at a time)
- Reduces 12-hour export to 1-2 hours for large candidate pools
- Automatic retry on network hiccups

### Crash Recovery
- If script stops (crash, network, manual interrupt): just run again
- Automatically skips already-downloaded resumes
- Checkpoint saved to `export_progress.json` (internal tracking)

### Progress Tracking (3 levels)
1. **Per-role** — `✓ Engineering → Senior SWE: 5 resumes`
2. **Per-department summary** — Shows count per department at end
3. **Overall %** — Shows progress every 100 applications
4. **Full log** — `export_progress.log` records everything with timestamps

### Failure Handling
- If any resume downloads fail: listed in `download_failures.csv` with error reason
- Can re-run to retry failed ones (successful downloads are skipped)
- Most failures are temporary (network); retry usually succeeds

## Important Details

### Resume File Names
Each file includes a Greenhouse attachment ID: `12345_jane_doe_att-456789.pdf`

**Why:** If a candidate uploaded multiple resumes, we need unique filenames so they don't overwrite each other. The attachment ID makes them unique.

### The Temporary "Partial Run" Folder
While the script is running, resumes download to `greenhouse_export_partial_run/`.

- **This is normal** — it's the working directory
- **Delete it after completion** — it can be large (100+ MB for big exports)
- **Final resumes are in** `greenhouse_export/resumes/` (this is what you keep)

### Why We Download Immediately
Greenhouse provides temporary download URLs that expire after ~7 days. We download resumes right away and save them as files, so:
- No expiry for you to worry about
- Files stay on your computer permanently
- CSV has actual file paths, not temporary URLs

### Re-running the Script
- **If it finishes normally:** You can run again; it will skip all already-downloaded resumes
- **If it crashes halfway:** Run again; it picks up where it left off
- **To retry failures:** Check `download_failures.csv`, then run again

## Troubleshooting

**"ERROR: Invalid username or token"**
- Wrong credentials entered
- Delete `.env` file and run again to re-enter

**Network timeouts during download**
- Normal for large exports; script retries automatically
- Check `download_failures.csv` for any that still failed
- Run again to retry failed ones

**"resumes_downloaded" shows "failed" for some**
- Network issue during that download
- Check `download_failures.csv` for error details
- Run again to retry

**Partial run folder is huge**
- Normal; it contains all resumes while downloading
- Safe to delete once main export completes
- (The final resumes in `greenhouse_export/resumes/` are kept)

## General Notes

- **No UI, no external services** — runs locally, talks only to Greenhouse
- **Fully automated** — no manual steps after entering credentials
- **One-time setup** — credentials saved, subsequent runs are instant
- **Large datasets supported** — tested with 1000+ candidates
- **Resumable** — survives crashes, network interruptions, manual stops

## License

MIT
