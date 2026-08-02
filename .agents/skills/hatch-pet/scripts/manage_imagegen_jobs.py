#!/usr/bin/env python3
"""Atomically inspect and advance a Hatch Pet image-generation job manifest."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from PIL import Image


MANIFEST_NAME = "imagegen-jobs.json"
LOCK_NAME = ".imagegen-jobs.lock"
VALID_STATUSES = {
    "pending",
    "running",
    "retry_wait",
    "complete",
    "failed_terminal",
}
DEFAULT_RETRY_POLICY = {
    "max_attempts": 3,
    "transport_backoff_seconds": [5, 15],
    "initial_concurrency": 3,
    "degraded_concurrency": 1,
    "degrade_after_consecutive_transport_failures": 2,
}
LIFECYCLE_CLEAR_FIELDS = {
    "claim",
    "completed_at",
    "last_error",
    "metadata",
    "next_attempt_at",
    "next_prompt_file",
    "reconciled_at",
    "reconciliation_required",
    "request_repair_used",
    "source_path",
}


class JobStateError(ValueError):
    """Raised when a requested job transition is unsafe or invalid."""


def parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise JobStateError(f"invalid timestamp: {value}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def safe_error_message(value: str) -> str:
    compact = " ".join(value.strip().split())
    compact = re.sub(
        r"(?:/Users|/home|/private|/var/folders)/[^\s,;]+",
        "<local-path>",
        compact,
    )
    compact = re.sub(r"[A-Za-z]:\\[^\s,;]+", "<local-path>", compact)
    return compact[:240] or "unspecified external generation error"


def atomic_write_json(path: Path, value: dict[str, object]) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def atomic_copy(source: Path, destination: Path) -> None:
    source = source.resolve()
    destination = destination.resolve()
    if source == destination:
        if not destination.is_file():
            raise JobStateError("declared job output does not exist")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    os.close(descriptor)
    try:
        shutil.copy2(source, temporary_name)
        with open(temporary_name, "rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary_name, destination)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_metadata(path: Path) -> dict[str, object]:
    if not path.is_file() or path.stat().st_size == 0:
        raise JobStateError("job output is missing or empty")
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            return {
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "format": image.format,
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
    except OSError as exc:
        raise JobStateError("job output is not a readable image") from exc


def manifest_path(run_dir: Path) -> Path:
    return run_dir / MANIFEST_NAME


def load_raw_manifest(run_dir: Path) -> dict[str, object]:
    path = manifest_path(run_dir)
    if not path.is_file():
        raise JobStateError(f"job manifest not found: {MANIFEST_NAME}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise JobStateError("job manifest is not valid JSON") from exc
    if not isinstance(value, dict):
        raise JobStateError("job manifest must be a JSON object")
    return value


def normalize_manifest(value: dict[str, object]) -> dict[str, object]:
    schema_version = value.get("schema_version", 1)
    if schema_version not in {1, 2}:
        raise JobStateError(f"unsupported job manifest schema: {schema_version}")
    if schema_version == 1:
        value["migrated_from_schema_version"] = 1
    value["schema_version"] = 2
    value["revision"] = int(value.get("revision", 0))
    retry_policy = value.get("retry_policy")
    if not isinstance(retry_policy, dict):
        retry_policy = {}
    value["retry_policy"] = {**DEFAULT_RETRY_POLICY, **retry_policy}
    scheduler = value.get("scheduler")
    if not isinstance(scheduler, dict):
        scheduler = {}
    scheduler.setdefault("consecutive_transport_failures", 0)
    scheduler.setdefault("degraded", False)
    value["scheduler"] = scheduler

    jobs = value.get("jobs")
    if not isinstance(jobs, list):
        raise JobStateError("job manifest jobs must be a list")
    seen = set()
    for job in jobs:
        if not isinstance(job, dict) or not isinstance(job.get("id"), str):
            raise JobStateError("every job must be an object with a string id")
        job_id = str(job["id"])
        if job_id in seen:
            raise JobStateError(f"duplicate job id: {job_id}")
        seen.add(job_id)
        status = str(job.get("status", "pending"))
        if status not in VALID_STATUSES:
            raise JobStateError(f"job {job_id} has invalid status: {status}")
        job["status"] = status
        attempts = job.get("attempts")
        if not isinstance(attempts, list):
            attempts = []
        job["attempts"] = attempts
        job["attempt_count"] = int(job.get("attempt_count", len(attempts)))
        job["max_attempts"] = int(
            job.get("max_attempts", value["retry_policy"]["max_attempts"])
        )
    return value


def jobs_by_id(manifest: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(job["id"]): job for job in manifest["jobs"]}


def declared_output(run_dir: Path, job: dict[str, object]) -> Path:
    raw = job.get("output_path")
    if not isinstance(raw, str) or not raw:
        raise JobStateError(f"job {job['id']} has no output_path")
    output = (run_dir / raw).resolve()
    try:
        output.relative_to(run_dir.resolve())
    except ValueError as exc:
        raise JobStateError(f"job {job['id']} output_path escapes the run") from exc
    return output


def refresh_reconciliation_flags(
    manifest: dict[str, object],
    run_dir: Path,
) -> None:
    for job in manifest["jobs"]:
        output = declared_output(run_dir, job)
        if job["status"] in {"pending", "retry_wait", "failed_terminal"} and output.is_file():
            job["reconciliation_required"] = True
        elif not output.is_file():
            job.pop("reconciliation_required", None)
        if job["status"] == "complete" and not output.is_file():
            job["output_missing"] = True
        else:
            job.pop("output_missing", None)


@contextmanager
def locked_manifest(
    run_dir: Path,
    *,
    exclusive: bool,
) -> Iterator[dict[str, object]]:
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        raise JobStateError("run directory does not exist")
    lock_path = run_dir / LOCK_NAME
    with lock_path.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        manifest = normalize_manifest(load_raw_manifest(run_dir))
        refresh_reconciliation_flags(manifest, run_dir)
        yield manifest
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def find_job(
    manifest: dict[str, object],
    job_id: str,
) -> dict[str, object]:
    job = jobs_by_id(manifest).get(job_id)
    if job is None:
        raise JobStateError(f"unknown job id: {job_id}")
    return job


def dependencies_complete(
    manifest: dict[str, object],
    job: dict[str, object],
) -> bool:
    by_id = jobs_by_id(manifest)
    dependencies = job.get("depends_on", [])
    if not isinstance(dependencies, list):
        raise JobStateError(f"job {job['id']} depends_on must be a list")
    return all(
        dependency in by_id and by_id[dependency]["status"] == "complete"
        for dependency in dependencies
    )


def is_retry_due(job: dict[str, object], now: datetime) -> bool:
    if job["status"] != "retry_wait":
        return True
    next_attempt = job.get("next_attempt_at")
    return not next_attempt or parse_time(str(next_attempt)) <= now


def recover_expired_claims(
    manifest: dict[str, object],
    now: datetime,
) -> list[str]:
    """Recover abandoned worker leases without granting extra attempts."""
    recovered = []
    for job in manifest["jobs"]:
        if job["status"] != "running":
            continue
        claim = job.get("claim")
        if not isinstance(claim, dict) or not claim.get("expires_at"):
            raise JobStateError(f"running job {job['id']} has no valid claim lease")
        if parse_time(str(claim["expires_at"])) > now:
            continue
        token = str(claim.get("token", ""))
        if not token:
            raise JobStateError(f"running job {job['id']} has no claim token")
        retryable = job["attempt_count"] < job["max_attempts"]
        error = {
            "category": "interruption",
            "code": "claim_expired",
            "safe_message": (
                "Worker claim expired before completion; resume from the same prompt."
            ),
            "observed_at": iso_time(now),
            "retryable": retryable,
        }
        job["last_error"] = error
        job.pop("claim", None)
        if retryable:
            job["status"] = "retry_wait"
            job["next_attempt_at"] = iso_time(now)
            attempts = job.get("attempts", [])
            last_attempt = attempts[-1] if attempts else {}
            job["next_prompt_file"] = (
                last_attempt.get("prompt_file")
                if isinstance(last_attempt, dict)
                else job.get("prompt_file")
            ) or job.get("prompt_file")
        else:
            job["status"] = "failed_terminal"
            job.pop("next_attempt_at", None)
            job.pop("next_prompt_file", None)
        finish_attempt(
            job,
            token,
            outcome=(
                "retryable-interruption" if retryable else "terminal-interruption"
            ),
            now=now,
        )
        recovered.append(str(job["id"]))
    return recovered


def ready_jobs(
    manifest: dict[str, object],
    run_dir: Path,
    now: datetime,
) -> list[dict[str, object]]:
    refresh_reconciliation_flags(manifest, run_dir)
    return [
        job
        for job in manifest["jobs"]
        if job["status"] in {"pending", "retry_wait"}
        and not job.get("reconciliation_required")
        and is_retry_due(job, now)
        and dependencies_complete(manifest, job)
    ]


def recommended_concurrency(manifest: dict[str, object]) -> int:
    policy = manifest["retry_policy"]
    return int(
        policy["degraded_concurrency"]
        if manifest["scheduler"].get("degraded")
        else policy["initial_concurrency"]
    )


def running_job_count(manifest: dict[str, object]) -> int:
    return sum(job["status"] == "running" for job in manifest["jobs"])


def available_concurrency_slots(manifest: dict[str, object]) -> int:
    return max(0, recommended_concurrency(manifest) - running_job_count(manifest))


def write_mutation(
    run_dir: Path,
    manifest: dict[str, object],
    now: datetime,
) -> None:
    manifest["schema_version"] = 2
    manifest["revision"] = int(manifest.get("revision", 0)) + 1
    manifest["updated_at"] = iso_time(now)
    atomic_write_json(manifest_path(run_dir), manifest)


def status_payload(
    manifest: dict[str, object],
    run_dir: Path,
    now: datetime,
) -> dict[str, object]:
    refresh_reconciliation_flags(manifest, run_dir)
    output = []
    for job in manifest["jobs"]:
        display_status = job["status"]
        if job.get("reconciliation_required"):
            display_status = "orphan-output"
        elif job.get("output_missing"):
            display_status = "output-missing"
        elif job["status"] == "failed_terminal":
            display_status = "failed"
        elif job["status"] == "retry_wait" and is_retry_due(job, now):
            display_status = "retrying"
        elif job.get("last_error", {}).get("code") == "http_408":
            display_status = "timeout"
        elif job["status"] == "retry_wait":
            display_status = "retry-wait"
        output.append(
            {
                "id": job["id"],
                "status": job["status"],
                "display_status": display_status,
                "attempt_count": job["attempt_count"],
                "max_attempts": job["max_attempts"],
                "next_attempt_at": job.get("next_attempt_at"),
                "last_error": job.get("last_error"),
                "reconciliation_required": bool(job.get("reconciliation_required")),
            }
        )
    return {
        "ok": True,
        "schema_version": manifest["schema_version"],
        "revision": manifest["revision"],
        "recommended_concurrency": recommended_concurrency(manifest),
        "running_jobs": running_job_count(manifest),
        "available_slots": available_concurrency_slots(manifest),
        "jobs": output,
    }


def verify_claim(job: dict[str, object], token: str) -> None:
    claim = job.get("claim")
    if job["status"] != "running" or not isinstance(claim, dict):
        raise JobStateError(f"job {job['id']} is not running")
    if claim.get("token") != token:
        raise JobStateError(f"job {job['id']} claim token does not match")


def finish_attempt(
    job: dict[str, object],
    token: str,
    *,
    outcome: str,
    now: datetime,
) -> None:
    for attempt in reversed(job["attempts"]):
        if isinstance(attempt, dict) and attempt.get("token") == token:
            attempt["outcome"] = outcome
            attempt["finished_at"] = iso_time(now)
            return
    raise JobStateError(f"job {job['id']} has no attempt for the claim token")


def claimed_prompt_file(job: dict[str, object], token: str) -> str:
    for attempt in reversed(job["attempts"]):
        if isinstance(attempt, dict) and attempt.get("token") == token:
            prompt_file = attempt.get("prompt_file")
            if isinstance(prompt_file, str) and prompt_file:
                return prompt_file
            break
    raise JobStateError(f"job {job['id']} claim has no prompt file")


def claim_job(
    manifest: dict[str, object],
    run_dir: Path,
    job_id: str,
    worker_id: str,
    now: datetime,
) -> dict[str, object]:
    job = find_job(manifest, job_id)
    if available_concurrency_slots(manifest) < 1:
        raise JobStateError(
            "image-generation concurrency limit reached; wait for a running job "
            "to complete or fail before claiming another"
        )
    if job not in ready_jobs(manifest, run_dir, now):
        raise JobStateError(f"job {job_id} is not ready")
    if job["attempt_count"] >= job["max_attempts"]:
        raise JobStateError(f"job {job_id} has exhausted its attempts")
    token = uuid.uuid4().hex
    prompt_file = str(job.get("next_prompt_file") or job.get("prompt_file"))
    job.pop("next_prompt_file", None)
    job["attempt_count"] += 1
    job["status"] = "running"
    job.pop("next_attempt_at", None)
    job["claim"] = {
        "token": token,
        "worker_id": worker_id,
        "claimed_at": iso_time(now),
        "expires_at": iso_time(now + timedelta(minutes=30)),
    }
    job["attempts"].append(
        {
            "number": job["attempt_count"],
            "token": token,
            "prompt_file": prompt_file,
            "input_images": job.get("input_images", []),
            "started_at": iso_time(now),
            "outcome": "running",
        }
    )
    return {
        "ok": True,
        "job_id": job_id,
        "claim_token": token,
        "attempt": job["attempt_count"],
        "prompt_file": prompt_file,
        "input_images": job.get("input_images", []),
        "output_path": job.get("output_path"),
    }


def complete_job(
    manifest: dict[str, object],
    run_dir: Path,
    job_id: str,
    token: str,
    source: Path,
    now: datetime,
) -> dict[str, object]:
    job = find_job(manifest, job_id)
    verify_claim(job, token)
    if not source.is_file():
        raise JobStateError("selected source output does not exist")
    output = declared_output(run_dir, job)
    atomic_copy(source, output)
    metadata = image_metadata(output)
    if job_id == "base":
        atomic_copy(output, run_dir / "references" / "canonical-base.png")
    finish_attempt(job, token, outcome="complete", now=now)
    job["status"] = "complete"
    job["completed_at"] = iso_time(now)
    job["source_path"] = str(source.resolve())
    job["metadata"] = metadata
    for field in ("claim", "last_error", "next_attempt_at", "reconciliation_required"):
        job.pop(field, None)
    manifest["scheduler"]["consecutive_transport_failures"] = 0
    manifest["scheduler"]["degraded"] = False
    return {
        "ok": True,
        "job_id": job_id,
        "status": "complete",
        "output_path": str(job["output_path"]),
        "metadata": metadata,
    }


def fail_job(
    manifest: dict[str, object],
    job_id: str,
    token: str,
    category: str,
    code: str,
    message: str,
    now: datetime,
) -> dict[str, object]:
    job = find_job(manifest, job_id)
    verify_claim(job, token)
    error = {
        "category": category,
        "code": code,
        "safe_message": safe_error_message(message),
        "observed_at": iso_time(now),
    }
    job["last_error"] = error
    job.pop("claim", None)
    policy = manifest["retry_policy"]
    retryable = False

    if category == "transport" and job["attempt_count"] < job["max_attempts"]:
        delays = list(policy["transport_backoff_seconds"])
        delay = int(delays[min(job["attempt_count"] - 1, len(delays) - 1)])
        job["status"] = "retry_wait"
        job["next_attempt_at"] = iso_time(now + timedelta(seconds=delay))
        job["next_prompt_file"] = claimed_prompt_file(job, token)
        retryable = True
        scheduler = manifest["scheduler"]
        scheduler["consecutive_transport_failures"] = int(
            scheduler.get("consecutive_transport_failures", 0)
        ) + 1
        if scheduler["consecutive_transport_failures"] >= int(
            policy["degrade_after_consecutive_transport_failures"]
        ):
            scheduler["degraded"] = True
    elif (
        category == "request"
        and job.get("retry_prompt_file")
        and not job.get("request_repair_used")
        and job["attempt_count"] < job["max_attempts"]
    ):
        job["status"] = "retry_wait"
        job["next_attempt_at"] = iso_time(now)
        job["next_prompt_file"] = job["retry_prompt_file"]
        job["request_repair_used"] = True
        retryable = True
        manifest["scheduler"]["consecutive_transport_failures"] = 0
    else:
        job["status"] = "failed_terminal"
        job.pop("next_attempt_at", None)
        job.pop("next_prompt_file", None)
        if category != "transport":
            manifest["scheduler"]["consecutive_transport_failures"] = 0

    error["retryable"] = retryable
    finish_attempt(
        job,
        token,
        outcome="retryable-failure" if retryable else "terminal-failure",
        now=now,
    )
    return {
        "ok": True,
        "job_id": job_id,
        "status": job["status"],
        "attempt_count": job["attempt_count"],
        "next_attempt_at": job.get("next_attempt_at"),
        "last_error": error,
        "recommended_concurrency": recommended_concurrency(manifest),
    }


def reconcile_payload(
    manifest: dict[str, object],
    run_dir: Path,
) -> dict[str, object]:
    refresh_reconciliation_flags(manifest, run_dir)
    findings = []
    for job in manifest["jobs"]:
        if job.get("reconciliation_required"):
            findings.append(
                {
                    "job_id": job["id"],
                    "code": "orphan_output",
                    "output_path": job["output_path"],
                    "next": "inspect then run reconcile --apply --job <id>, or reset explicitly",
                }
            )
        elif job.get("output_missing"):
            findings.append(
                {
                    "job_id": job["id"],
                    "code": "completed_output_missing",
                    "output_path": job["output_path"],
                    "next": "restore the output or reset the job explicitly",
                }
            )
    return {"ok": not findings, "findings": findings}


def reconcile_job(
    manifest: dict[str, object],
    run_dir: Path,
    job_id: str,
    now: datetime,
) -> dict[str, object]:
    job = find_job(manifest, job_id)
    output = declared_output(run_dir, job)
    if job["status"] == "running":
        raise JobStateError(
            "cannot reconcile an actively claimed job; complete, fail, or wait for lease expiry"
        )
    if job["status"] == "complete" and not output.is_file():
        raise JobStateError("completed output is missing; restore it or reset explicitly")
    if job["status"] == "complete":
        return {"ok": True, "job_id": job_id, "status": "complete", "changed": False}
    metadata = image_metadata(output)
    if job_id == "base":
        atomic_copy(output, run_dir / "references" / "canonical-base.png")
    job["status"] = "complete"
    job["completed_at"] = iso_time(now)
    job["source_path"] = "reconciled-existing-output"
    job["metadata"] = metadata
    job["reconciled_at"] = iso_time(now)
    for field in ("claim", "last_error", "next_attempt_at", "reconciliation_required"):
        job.pop(field, None)
    manifest["scheduler"]["consecutive_transport_failures"] = 0
    manifest["scheduler"]["degraded"] = False
    return {
        "ok": True,
        "job_id": job_id,
        "status": "complete",
        "changed": True,
        "metadata": metadata,
    }


def dependent_ids(manifest: dict[str, object], root_id: str) -> set[str]:
    dependents = set()
    changed = True
    while changed:
        changed = False
        for job in manifest["jobs"]:
            job_id = str(job["id"])
            dependencies = set(job.get("depends_on", []))
            if job_id not in dependents and dependencies & ({root_id} | dependents):
                dependents.add(job_id)
                changed = True
    return dependents


def reset_jobs(
    manifest: dict[str, object],
    run_dir: Path,
    job_id: str,
    reason: str,
    cascade: bool,
    now: datetime,
) -> dict[str, object]:
    find_job(manifest, job_id)
    dependents = dependent_ids(manifest, job_id)
    active_dependents = {
        dependent
        for dependent in dependents
        if find_job(manifest, dependent)["status"] != "pending"
        or declared_output(run_dir, find_job(manifest, dependent)).is_file()
    }
    if active_dependents and not cascade:
        raise JobStateError(
            "dependent jobs have progress; pass --cascade to reset them explicitly"
        )
    targets = {job_id} | (dependents if cascade else set())
    archived = []
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    for target in sorted(targets):
        job = find_job(manifest, target)
        output = declared_output(run_dir, job)
        if output.is_file():
            archive = run_dir / "recovery-archive" / f"{target}-{timestamp}{output.suffix}"
            archive.parent.mkdir(parents=True, exist_ok=True)
            os.replace(output, archive)
            archived.append(str(archive.relative_to(run_dir)))
        if target == "base":
            canonical = run_dir / "references" / "canonical-base.png"
            if canonical.is_file():
                canonical_archive = (
                    run_dir
                    / "recovery-archive"
                    / f"base-canonical-{timestamp}{canonical.suffix}"
                )
                canonical_archive.parent.mkdir(parents=True, exist_ok=True)
                os.replace(canonical, canonical_archive)
                archived.append(str(canonical_archive.relative_to(run_dir)))
        history = job.get("reset_history")
        if not isinstance(history, list):
            history = []
        history.append(
            {
                "reset_at": iso_time(now),
                "reason": reason,
                "previous_status": job["status"],
                "previous_attempt_count": job["attempt_count"],
            }
        )
        for field in LIFECYCLE_CLEAR_FIELDS:
            job.pop(field, None)
        job["status"] = "pending"
        job["attempt_count"] = 0
        job["attempts"] = []
        job["reset_history"] = history
    return {
        "ok": True,
        "reset_jobs": sorted(targets),
        "archived_outputs": archived,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--now", help="Inject an ISO-8601 clock for deterministic checks.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status")
    ready_parser = subparsers.add_parser("ready")
    ready_parser.add_argument("--limit", type=int)

    claim_parser = subparsers.add_parser("claim")
    claim_parser.add_argument("--job", required=True)
    claim_parser.add_argument("--worker-id", required=True)

    complete_parser = subparsers.add_parser("complete")
    complete_parser.add_argument("--job", required=True)
    complete_parser.add_argument("--claim-token", required=True)
    complete_parser.add_argument("--source", required=True)

    fail_parser = subparsers.add_parser("fail")
    fail_parser.add_argument("--job", required=True)
    fail_parser.add_argument("--claim-token", required=True)
    fail_parser.add_argument(
        "--category",
        required=True,
        choices=("transport", "request", "semantic", "validation", "cancelled"),
    )
    fail_parser.add_argument("--code", required=True)
    fail_parser.add_argument("--message", required=True)

    reconcile_parser = subparsers.add_parser("reconcile")
    reconcile_parser.add_argument("--apply", action="store_true")
    reconcile_parser.add_argument("--job")

    reset_parser = subparsers.add_parser("reset")
    reset_parser.add_argument("--job", required=True)
    reset_parser.add_argument("--reason", required=True)
    reset_parser.add_argument("--cascade", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    now = parse_time(args.now)
    mutating = args.command in {"claim", "complete", "fail", "reset"} or (
        args.command == "reconcile" and args.apply
    )
    recovers_expired_claims = args.command in {"status", "ready"}

    try:
        with locked_manifest(
            run_dir,
            exclusive=mutating or recovers_expired_claims,
        ) as manifest:
            recovered = (
                recover_expired_claims(manifest, now)
                if recovers_expired_claims
                else []
            )
            if args.command == "status":
                result = status_payload(manifest, run_dir, now)
            elif args.command == "ready":
                available = ready_jobs(manifest, run_dir, now)
                slots = available_concurrency_slots(manifest)
                limit = slots
                if args.limit is not None:
                    if args.limit < 1:
                        raise JobStateError("--limit must be positive")
                    limit = min(limit, args.limit)
                result = {
                    "ok": True,
                    "recommended_concurrency": recommended_concurrency(manifest),
                    "running_jobs": running_job_count(manifest),
                    "available_slots": slots,
                    "ready_jobs": [job["id"] for job in available[:limit]],
                }
            elif args.command == "claim":
                result = claim_job(
                    manifest,
                    run_dir,
                    args.job,
                    args.worker_id,
                    now,
                )
            elif args.command == "complete":
                result = complete_job(
                    manifest,
                    run_dir,
                    args.job,
                    args.claim_token,
                    Path(args.source).expanduser().resolve(),
                    now,
                )
            elif args.command == "fail":
                result = fail_job(
                    manifest,
                    args.job,
                    args.claim_token,
                    args.category,
                    args.code,
                    args.message,
                    now,
                )
            elif args.command == "reconcile" and args.apply:
                if not args.job:
                    raise JobStateError("reconcile --apply requires --job")
                result = reconcile_job(manifest, run_dir, args.job, now)
            elif args.command == "reconcile":
                result = reconcile_payload(manifest, run_dir)
            else:
                result = reset_jobs(
                    manifest,
                    run_dir,
                    args.job,
                    args.reason,
                    args.cascade,
                    now,
                )

            if recovered:
                result["recovered_expired_claims"] = recovered
            if mutating or recovered:
                write_mutation(run_dir, manifest, now)
                if "revision" in result:
                    result["revision"] = manifest["revision"]
        print(json.dumps(result, indent=2))
    except JobStateError as exc:
        raise SystemExit(f"ERROR: {exc}") from exc


if __name__ == "__main__":
    main()
