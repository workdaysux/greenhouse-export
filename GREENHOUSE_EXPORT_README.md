# Greenhouse ATS Export Tool

One-time export of all candidates, applications, and resumes from a Greenhouse instance.

## What it does

- Exports all candidate + application data to CSV (with job, department, status, stage)
- Downloads all resumes organized by department → role
- Handles large datasets with cursor pagination

## Requirements

- Python 3.7+
- Greenhouse API credentials (v3 OAuth2 + v1 Basic)

## Setup

### 1. Get Greenhouse API Credentials

In your Greenhouse account:
1. Go **Settings → API Credentials** 
2. Create a v3 OAuth2 app (client ID + secret)
3. Note your **User ID** (Settings → Account, top-right)

### 2. Set Environment Variables

Run the script and it will guide you through entering your credentials:

```bash
bash greenhouse_export.sh
```

Or create a `.env` file manually:
```bash
# .env
GREENHOUSE_V3_CLIENT_ID=your_client_id
GREENHOUSE_V3_CLIENT_SECRET=your_client_secret
GREENHOUSE_USER_ID=your_user_id
```

### 3. Run

```bash
python3 greenhouse_export.py
```

## Output

```
greenhouse_export/
├── export_candidates.csv
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

**CSV columns:**
- candidate_id, first_name, last_name, email, phone
- job_id, job_name, department
- application_status, stage
- created_at, updated_at
- tags, resumes_downloaded

## Notes

- First run: Interactive wizard guides you through adding credentials (saved for next time)
- Resumes have pre-signed URLs that expire in ~7 days — download immediately
- Large datasets (1000+ candidates) may take 5-10 minutes
- Script pauses briefly to respect rate limits (50 req/10 sec)
- All candidate data is fetched locally — no third-party services used
