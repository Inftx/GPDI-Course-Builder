import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

JOB_STATUS_PENDING = "Pending"
JOB_STATUS_RUNNING = "Running"
JOB_STATUS_COMPLETED = "Completed"
JOB_STATUS_FAILED = "Failed"

_PROJECTS_FOLDER = Path("projects")
_LOCK = threading.Lock()


def _ensure_jobs_folder(project_name: str) -> Path:
    project_folder = _PROJECTS_FOLDER / project_name
    jobs_folder = project_folder / "jobs"
    jobs_folder.mkdir(parents=True, exist_ok=True)
    return jobs_folder


def _jobs_file_path(project_name: str) -> Path:
    jobs_folder = _ensure_jobs_folder(project_name)
    return jobs_folder / "jobs.json"


def _load_jobs(project_name: str) -> list[dict[str, Any]]:
    jobs_file = _jobs_file_path(project_name)

    if not jobs_file.exists():
        return []

    with jobs_file.open("r", encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError:
            return []


def _save_jobs(project_name: str, jobs: list[dict[str, Any]]) -> None:
    jobs_file = _jobs_file_path(project_name)

    with _LOCK:
        with jobs_file.open("w", encoding="utf-8") as handle:
            json.dump(jobs, handle, indent=4, ensure_ascii=False)


def _find_job(project_name: str, job_id: str) -> dict[str, Any] | None:
    for job in _load_jobs(project_name):
        if job.get("job_id") == job_id:
            return job
    return None


def create_job(project_name: str, task_type: str, output_file: str | None = None) -> dict[str, Any]:
    job_id = str(uuid4())
    job = {
        "job_id": job_id,
        "project_name": project_name,
        "task_type": task_type,
        "status": JOB_STATUS_PENDING,
        "started_at": None,
        "completed_at": None,
        "output_file": output_file,
        "error_message": None,
    }

    jobs = _load_jobs(project_name)
    jobs.append(job)
    _save_jobs(project_name, jobs)
    return job


def start_job(project_name: str, job_id: str) -> dict[str, Any] | None:
    jobs = _load_jobs(project_name)
    updated = False

    for job in jobs:
        if job.get("job_id") == job_id:
            job["status"] = JOB_STATUS_RUNNING
            job["started_at"] = datetime.utcnow().isoformat() + "Z"
            updated = True
            break

    if not updated:
        return None

    _save_jobs(project_name, jobs)
    return _find_job(project_name, job_id)


def complete_job(project_name: str, job_id: str, output_file: str | None = None) -> dict[str, Any] | None:
    jobs = _load_jobs(project_name)
    updated = False

    for job in jobs:
        if job.get("job_id") == job_id:
            job["status"] = JOB_STATUS_COMPLETED
            job["completed_at"] = datetime.utcnow().isoformat() + "Z"
            if output_file is not None:
                job["output_file"] = output_file
            updated = True
            break

    if not updated:
        return None

    _save_jobs(project_name, jobs)
    return _find_job(project_name, job_id)


def fail_job(project_name: str, job_id: str, error_message: str) -> dict[str, Any] | None:
    jobs = _load_jobs(project_name)
    updated = False

    for job in jobs:
        if job.get("job_id") == job_id:
            job["status"] = JOB_STATUS_FAILED
            job["completed_at"] = datetime.utcnow().isoformat() + "Z"
            job["error_message"] = error_message
            updated = True
            break

    if not updated:
        return None

    _save_jobs(project_name, jobs)
    return _find_job(project_name, job_id)


def list_jobs(project_name: str) -> list[dict[str, Any]]:
    return _load_jobs(project_name)


def get_job(job_id: str) -> dict[str, Any] | None:
    project_folders = [_PROJECTS_FOLDER / folder.name for folder in _PROJECTS_FOLDER.iterdir() if folder.is_dir()]

    for project_path in project_folders:
        jobs_file = project_path / "jobs" / "jobs.json"
        if not jobs_file.exists():
            continue

        with jobs_file.open("r", encoding="utf-8") as handle:
            try:
                jobs = json.load(handle)
            except json.JSONDecodeError:
                continue

        for job in jobs:
            if job.get("job_id") == job_id:
                return job
    return None
