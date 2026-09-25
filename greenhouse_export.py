#!/usr/bin/env python3
"""
Greenhouse ATS export: all candidates + applications + jobs + resumes by role/dept.
Outputs: export_candidates.csv + resumes/ directory structure.
"""

import os
import sys
import json
import csv
import urllib.request
import urllib.error
import base64
from urllib.parse import urlparse
from pathlib import Path
from datetime import datetime

# Get credentials from env
V3_CLIENT_ID = os.getenv("GREENHOUSE_V3_CLIENT_ID")
V3_CLIENT_SECRET = os.getenv("GREENHOUSE_V3_CLIENT_SECRET")
GREENHOUSE_USER_ID = os.getenv("GREENHOUSE_USER_ID")

if not all([V3_CLIENT_ID, V3_CLIENT_SECRET, GREENHOUSE_USER_ID]):
    print("ERROR: Missing Greenhouse credentials. Set:")
    print("  GREENHOUSE_V3_CLIENT_ID")
    print("  GREENHOUSE_V3_CLIENT_SECRET")
    print("  GREENHOUSE_USER_ID")
    sys.exit(1)

OUTPUT_DIR = Path.cwd() / "greenhouse_export"
OUTPUT_DIR.mkdir(exist_ok=True)
RESUME_DIR = OUTPUT_DIR / "resumes"
RESUME_DIR.mkdir(exist_ok=True)

# ============================================================================
# v3 OAuth2 Token
# ============================================================================

def get_v3_token():
    """Get v3 Bearer token."""
    url = "https://auth.greenhouse.io/token?grant_type=client_credentials"
    auth_str = base64.b64encode(f"{V3_CLIENT_ID}:{V3_CLIENT_SECRET}".encode()).decode()
    payload = json.dumps({"sub": int(GREENHOUSE_USER_ID)}).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Basic {auth_str}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        print(f"✓ Got v3 token (expires in {data.get('expires_in', 3600)}s)")
        return data["access_token"]
    except urllib.error.HTTPError as e:
        print(f"ERROR getting token: {e.read().decode()}")
        sys.exit(1)

# ============================================================================
# v3 Cursor Pagination
# ============================================================================

def fetch_v3_paginated(token, endpoint, per_page=500):
    """Fetch all records from a v3 endpoint using cursor pagination."""
    results = []
    url = f"https://harvest.greenhouse.io/v3{endpoint}?per_page={per_page}"

    while url:
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}"},
        )

        try:
            resp = urllib.request.urlopen(req)
            data = json.loads(resp.read())

            # Endpoint returns either {data: [...]} or [...] directly
            if isinstance(data, dict) and "data" in data:
                results.extend(data["data"])
                # Get next cursor from Link header
                link = resp.headers.get("Link", "")
                url = None
                if 'rel="next"' in link:
                    for part in link.split(","):
                        if 'rel="next"' in part:
                            url = part.split("<")[1].split(">")[0]
                            break
            elif isinstance(data, list):
                results.extend(data)
                url = None
            else:
                results.append(data)
                url = None

            print(f"  Fetched {len(results)} records from {endpoint}")
        except urllib.error.HTTPError as e:
            print(f"ERROR fetching {url}: {e.status} {e.read().decode()}")
            sys.exit(1)

    return results

# ============================================================================
# Download Resumes
# ============================================================================

def download_resume(candidate_id, candidate_name, role_name, dept_name, resume_url, resume_filename):
    """Download resume and organize by role/dept."""
    # Sanitize names for filesystem
    def safe_name(s):
        return "".join(c if c.isalnum() or c in " -_" else "_" for c in s).strip()

    dept_dir = RESUME_DIR / safe_name(dept_name) if dept_name else RESUME_DIR / "Other"
    role_dir = dept_dir / safe_name(role_name) if role_name else dept_dir / "Other"
    role_dir.mkdir(parents=True, exist_ok=True)

    # Filename: candidate_id_name_ext
    ext = Path(resume_filename).suffix or ".pdf"
    local_filename = f"{candidate_id}_{safe_name(candidate_name)}{ext}"
    local_path = role_dir / local_filename

    try:
        req = urllib.request.Request(resume_url)
        with urllib.request.urlopen(req) as resp:
            with open(local_path, "wb") as f:
                f.write(resp.read())
        print(f"    ✓ Downloaded: {role_dir.relative_to(OUTPUT_DIR)}/{local_filename}")
        return str(local_path)
    except Exception as e:
        print(f"    ✗ Failed to download {resume_filename}: {e}")
        return None

# ============================================================================
# Main Export
# ============================================================================

def main():
    print("\n=== GREENHOUSE EXPORT ===\n")

    token = get_v3_token()

    # Fetch all data
    print("\nFetching candidates...")
    candidates = fetch_v3_paginated(token, "/candidates")
    print(f"  Total: {len(candidates)} candidates\n")

    print("Fetching applications...")
    applications = fetch_v3_paginated(token, "/applications")
    print(f"  Total: {len(applications)} applications\n")

    print("Fetching jobs...")
    jobs = fetch_v3_paginated(token, "/jobs")
    print(f"  Total: {len(jobs)} jobs\n")

    print("Fetching attachments...")
    attachments = fetch_v3_paginated(token, "/attachments")
    print(f"  Total: {len(attachments)} attachments\n")

    print("Fetching interview stages...")
    stages = fetch_v3_paginated(token, "/job_interview_stages")
    print(f"  Total: {len(stages)} stages\n")

    # Build lookup dicts
    candidates_by_id = {c["id"]: c for c in candidates}
    jobs_by_id = {j["id"]: j for j in jobs}
    attachments_by_candidate = {}
    for att in attachments:
        cid = att["candidate_id"]
        if cid not in attachments_by_candidate:
            attachments_by_candidate[cid] = []
        attachments_by_candidate[cid].append(att)

    stages_by_id = {s["id"]: s for s in stages}

    # Build CSV rows
    csv_rows = []
    resume_count = 0

    print("Processing applications and downloading resumes...\n")
    for i, app in enumerate(applications, 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{len(applications)} applications...")

        candidate_id = app["candidate_id"]
        candidate = candidates_by_id.get(candidate_id, {})
        job = jobs_by_id.get(app["job_id"], {})
        stage = stages_by_id.get(app["stage_id"], {}) if app.get("stage_id") else {}

        # Get candidate name and contact
        first_name = candidate.get("first_name", "")
        last_name = candidate.get("last_name", "")
        candidate_name = f"{first_name} {last_name}".strip()

        emails = candidate.get("email_addresses", [])
        primary_email = emails[0]["value"] if emails else ""

        phones = candidate.get("phone_numbers", [])
        primary_phone = phones[0]["value"] if phones else ""

        # Application details
        job_name = job.get("name", "")
        job_id = app.get("job_id", "")
        departments = job.get("departments", [])
        dept_name = departments[0].get("name", "") if departments else ""

        stage_name = app.get("stage_name", "")
        status = app.get("status", "")
        created_at = app.get("created_at", "")
        updated_at = app.get("updated_at", "")

        # Download resumes
        resumes_downloaded = []
        app_attachments = attachments_by_candidate.get(candidate_id, [])
        for att in app_attachments:
            if att.get("type") == "resume" or "resume" in att.get("filename", "").lower():
                resume_path = download_resume(
                    candidate_id,
                    candidate_name,
                    job_name,
                    dept_name,
                    att["url"],
                    att["filename"],
                )
                if resume_path:
                    resumes_downloaded.append(att["filename"])
                    resume_count += 1

        # Row for CSV
        csv_rows.append({
            "candidate_id": candidate_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": primary_email,
            "phone": primary_phone,
            "job_id": job_id,
            "job_name": job_name,
            "department": dept_name,
            "application_status": status,
            "stage": stage_name,
            "created_at": created_at,
            "updated_at": updated_at,
            "tags": ", ".join(t["name"] for t in candidate.get("tags", [])),
            "resumes_downloaded": "; ".join(resumes_downloaded),
        })

    print(f"\n✓ Downloaded {resume_count} resumes\n")

    # Write CSV
    csv_path = OUTPUT_DIR / "export_candidates.csv"
    fieldnames = list(csv_rows[0].keys()) if csv_rows else []

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"✓ Wrote {len(csv_rows)} rows to {csv_path}")
    print(f"✓ Resumes organized in: {RESUME_DIR}")
    print(f"\n=== EXPORT COMPLETE ===")
    print(f"Output directory: {OUTPUT_DIR}\n")

if __name__ == "__main__":
    main()
