#!/usr/bin/env python3
"""
Greenhouse ATS export with crash recovery, parallel downloads, and detailed progress.
Outputs: export_candidates.csv + resumes/ directory.
Checkpoints to export_progress.json for resumability.
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
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

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
PARTIAL_DIR = Path.cwd() / "greenhouse_export_partial_run"
RESUME_DIR = OUTPUT_DIR / "resumes"
PARTIAL_RESUME_DIR = PARTIAL_DIR / "resumes"
PROGRESS_FILE = OUTPUT_DIR / "export_progress.json"
LOG_FILE = OUTPUT_DIR / "export_progress.log"
FAILURES_FILE = OUTPUT_DIR / "download_failures.csv"

OUTPUT_DIR.mkdir(exist_ok=True)
PARTIAL_DIR.mkdir(exist_ok=True)
RESUME_DIR.mkdir(exist_ok=True)
PARTIAL_RESUME_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Progress Tracking
# ============================================================================

class ProgressTracker:
    def __init__(self):
        self.log_file = open(LOG_FILE, "a")
        self.downloaded_resumes = set()
        self.failed_resumes = []
        self.dept_totals = defaultdict(int)
        self.role_totals = defaultdict(lambda: defaultdict(int))
        self.load_checkpoint()

    def log(self, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {msg}"
        print(log_line)
        self.log_file.write(log_line + "\n")
        self.log_file.flush()

    def save_checkpoint(self):
        checkpoint = {
            "downloaded_resumes": list(self.downloaded_resumes),
            "failed_resumes": self.failed_resumes,
            "last_updated": datetime.now().isoformat(),
        }
        with open(PROGRESS_FILE, "w") as f:
            json.dump(checkpoint, f, indent=2)

    def load_checkpoint(self):
        if PROGRESS_FILE.exists():
            try:
                with open(PROGRESS_FILE, "r") as f:
                    checkpoint = json.load(f)
                    self.downloaded_resumes = set(checkpoint.get("downloaded_resumes", []))
                    self.failed_resumes = checkpoint.get("failed_resumes", [])
                    self.log(f"✓ Resuming: {len(self.downloaded_resumes)} resumes downloaded, {len(self.failed_resumes)} failures")
            except Exception as e:
                self.log(f"⚠ Could not load checkpoint: {e}")

    def mark_downloaded(self, candidate_id, attachment_id):
        key = f"{candidate_id}_{attachment_id}"
        self.downloaded_resumes.add(key)
        self.save_checkpoint()

    def mark_failed(self, candidate_id, attachment_id, error):
        key = f"{candidate_id}_{attachment_id}"
        self.failed_resumes.append({"candidate_id": candidate_id, "attachment_id": attachment_id, "error": str(error)})
        self.save_checkpoint()

    def was_downloaded(self, candidate_id, attachment_id):
        key = f"{candidate_id}_{attachment_id}"
        return key in self.downloaded_resumes

    def add_dept_total(self, dept, count):
        self.dept_totals[dept] += count

    def add_role_total(self, dept, role, count):
        self.role_totals[dept][role] += count

    def close(self):
        self.log_file.close()

progress = ProgressTracker()

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
        progress.log(f"✓ Got v3 token (expires in {data.get('expires_in', 3600)}s)")
        return data["access_token"]
    except urllib.error.HTTPError as e:
        progress.log(f"ERROR getting token: {e.read().decode()}")
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

            if isinstance(data, dict) and "data" in data:
                results.extend(data["data"])
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
        except urllib.error.HTTPError as e:
            progress.log(f"ERROR fetching {url}: {e.status} {e.read().decode()}")
            sys.exit(1)

    return results

# ============================================================================
# Download Resumes (Parallel)
# ============================================================================

def download_resume(candidate_id, candidate_name, role_name, dept_name, attachment_id, resume_url, resume_filename):
    """Download single resume. Called by thread pool."""
    # Skip if already downloaded
    if progress.was_downloaded(candidate_id, attachment_id):
        return {"status": "skipped", "candidate_id": candidate_id, "attachment_id": attachment_id}

    def safe_name(s):
        return "".join(c if c.isalnum() or c in " -_" else "_" for c in s).strip()

    dept_dir = PARTIAL_RESUME_DIR / safe_name(dept_name) if dept_name else PARTIAL_RESUME_DIR / "Other"
    role_dir = dept_dir / safe_name(role_name) if role_name else dept_dir / "Other"
    role_dir.mkdir(parents=True, exist_ok=True)

    # Filename: candidate_id_name_attachment_id.ext
    ext = Path(resume_filename).suffix or ".pdf"
    local_filename = f"{candidate_id}_{safe_name(candidate_name)}_{attachment_id}{ext}"
    local_path = role_dir / local_filename

    try:
        req = urllib.request.Request(resume_url)
        with urllib.request.urlopen(req) as resp:
            with open(local_path, "wb") as f:
                f.write(resp.read())

        progress.mark_downloaded(candidate_id, attachment_id)
        progress.add_role_total(dept_name or "Other", role_name or "Other", 1)
        progress.add_dept_total(dept_name or "Other", 1)

        return {
            "status": "success",
            "candidate_id": candidate_id,
            "attachment_id": attachment_id,
            "filename": local_filename,
            "dept": dept_name or "Other",
            "role": role_name or "Other",
        }
    except Exception as e:
        progress.mark_failed(candidate_id, attachment_id, str(e))
        return {
            "status": "failed",
            "candidate_id": candidate_id,
            "attachment_id": attachment_id,
            "error": str(e),
        }

# ============================================================================
# Main Export
# ============================================================================

def main():
    progress.log("\n=== GREENHOUSE EXPORT (parallel downloads + crash recovery) ===\n")

    token = get_v3_token()

    # Fetch all data
    progress.log("\nFetching candidates...")
    candidates = fetch_v3_paginated(token, "/candidates")
    progress.log(f"  Total: {len(candidates)} candidates")

    progress.log("\nFetching applications...")
    applications = fetch_v3_paginated(token, "/applications")
    progress.log(f"  Total: {len(applications)} applications")

    progress.log("\nFetching jobs...")
    jobs = fetch_v3_paginated(token, "/jobs")
    progress.log(f"  Total: {len(jobs)} jobs")

    progress.log("\nFetching attachments...")
    attachments = fetch_v3_paginated(token, "/attachments")
    progress.log(f"  Total: {len(attachments)} attachments\n")

    # Build lookup dicts
    candidates_by_id = {c["id"]: c for c in candidates}
    jobs_by_id = {j["id"]: j for j in jobs}
    attachments_by_candidate = {}
    for att in attachments:
        cid = att["candidate_id"]
        if cid not in attachments_by_candidate:
            attachments_by_candidate[cid] = []
        attachments_by_candidate[cid].append(att)

    # Open CSV for streaming writes
    csv_path = OUTPUT_DIR / "export_candidates.csv"
    csv_file = open(csv_path, "w", newline="", encoding="utf-8")
    csv_fieldnames = [
        "candidate_id", "first_name", "last_name", "email", "phone",
        "job_id", "job_name", "department", "application_status", "stage",
        "created_at", "updated_at", "tags",
        "resume_files", "resumes_downloaded"
    ]
    csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fieldnames)
    csv_writer.writeheader()

    # Build list of downloads to queue
    download_queue = []
    csv_rows_by_app_id = {}

    progress.log("Preparing download queue...\n")
    for app in applications:
        candidate_id = app["candidate_id"]
        candidate = candidates_by_id.get(candidate_id, {})
        job = jobs_by_id.get(app["job_id"], {})

        first_name = candidate.get("first_name", "")
        last_name = candidate.get("last_name", "")
        candidate_name = f"{first_name} {last_name}".strip()

        emails = candidate.get("email_addresses", [])
        primary_email = emails[0]["value"] if emails else ""

        phones = candidate.get("phone_numbers", [])
        primary_phone = phones[0]["value"] if phones else ""

        job_name = job.get("name", "")
        job_id = app.get("job_id", "")
        departments = job.get("departments", [])
        dept_name = departments[0].get("name", "") if departments else ""

        stage_name = app.get("stage_name", "")
        status = app.get("status", "")
        created_at = app.get("created_at", "")
        updated_at = app.get("updated_at", "")

        # Build resume file list and queue downloads
        resume_files = []
        expected_resumes = []
        app_attachments = attachments_by_candidate.get(candidate_id, [])
        for att in app_attachments:
            if att.get("type") == "resume" or "resume" in att.get("filename", "").lower():
                attachment_id = att["id"]

                # Queue download
                download_queue.append({
                    "candidate_id": candidate_id,
                    "candidate_name": candidate_name,
                    "role_name": job_name,
                    "dept_name": dept_name,
                    "attachment_id": attachment_id,
                    "resume_url": att["url"],
                    "resume_filename": att["filename"],
                })

                def safe_name(s):
                    return "".join(c if c.isalnum() or c in " -_" else "_" for c in s).strip()

                ext = Path(att["filename"]).suffix or ".pdf"
                expected_filename = f"{candidate_id}_{safe_name(candidate_name)}_{attachment_id}{ext}"
                dept_safe = safe_name(dept_name or "Other")
                role_safe = safe_name(job_name or "Other")
                expected_path = f"resumes/{dept_safe}/{role_safe}/{expected_filename}"
                expected_resumes.append(expected_path)
                resume_files.append(att["filename"])

        # Write row with pending status
        csv_writer.writerow({
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
            "resume_files": "; ".join(expected_resumes) if expected_resumes else "",
            "resumes_downloaded": "pending" if expected_resumes else "none",
        })
        csv_file.flush()

        # Track for later updates
        csv_rows_by_app_id[app["id"]] = {
            "candidate_id": candidate_id,
            "expected_resumes": len(expected_resumes),
        }

    progress.log(f"Queued {len(download_queue)} resumes for parallel download\n")
    progress.log("Downloading with 8 concurrent workers...\n")

    # Parallel download with ThreadPoolExecutor
    download_results = defaultdict(list)
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(download_resume, **task): task["candidate_id"]
            for task in download_queue
        }

        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            candidate_id = result["candidate_id"]
            download_results[candidate_id].append(result)

            if completed % 10 == 0:
                pct = int((completed / len(download_queue)) * 100)
                progress.log(f"  [{pct}%] Downloaded {completed}/{len(download_queue)} resumes...")

    progress.log(f"\n✓ Downloaded {len(download_queue)} resumes\n")

    # Update CSV with final status
    progress.log("Updating CSV with download results...\n")
    csv_file.close()

    # Read and update CSV
    csv_data = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        csv_data = list(reader)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fieldnames)
        writer.writeheader()

        for row in csv_data:
            candidate_id = int(row["candidate_id"])
            results = download_results.get(candidate_id, [])

            if results:
                successes = [r for r in results if r["status"] == "success"]
                if successes:
                    row["resumes_downloaded"] = "yes"
                else:
                    row["resumes_downloaded"] = "failed"
            elif row["resumes_downloaded"] == "pending":
                row["resumes_downloaded"] = "failed"

            writer.writerow(row)

    # Write failures CSV
    if progress.failed_resumes:
        with open(FAILURES_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["candidate_id", "attachment_id", "error"])
            writer.writeheader()
            writer.writerows(progress.failed_resumes)
        progress.log(f"✓ Wrote {len(progress.failed_resumes)} failures to {FAILURES_FILE}\n")

    # Final department totals
    progress.log("=== DEPARTMENT SUMMARY ===")
    for dept, count in sorted(progress.dept_totals.items()):
        progress.log(f"  {dept}: {count} resumes")
        for role, role_count in sorted(progress.role_totals[dept].items()):
            progress.log(f"    → {role}: {role_count}")

    progress.log(f"\n✓ Wrote {len(csv_data)} rows to {csv_path}")
    progress.log(f"✓ Partial downloads in: {PARTIAL_DIR} (delete after completion)")
    progress.log(f"✓ Final resumes in: {RESUME_DIR}")
    progress.log(f"✓ Progress log: {LOG_FILE}")
    progress.log(f"\n=== EXPORT COMPLETE ===\n")
    progress.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        progress.log("\n⚠ Export interrupted. Run again to resume from checkpoint.")
        progress.close()
        sys.exit(1)
    except Exception as e:
        progress.log(f"\n❌ Error: {e}")
        progress.log("Run again to resume from checkpoint.")
        progress.close()
        sys.exit(1)
