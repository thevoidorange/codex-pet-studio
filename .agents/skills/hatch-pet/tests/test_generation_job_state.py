from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image


SKILL_DIR = Path(__file__).resolve().parents[1]
PREPARE = SKILL_DIR / "scripts" / "prepare_pet_run.py"
MANAGE = SKILL_DIR / "scripts" / "manage_imagegen_jobs.py"
START = datetime(2026, 8, 2, 0, 0, tzinfo=timezone.utc)


def timestamp(offset_seconds: int = 0) -> str:
    return (START + timedelta(seconds=offset_seconds)).isoformat()


class GenerationJobStateTest(unittest.TestCase):
    def prepare_run(self, root: Path) -> Path:
        run_dir = root / "run"
        completed = subprocess.run(
            [
                sys.executable,
                str(PREPARE),
                "--pet-name",
                "Synthetic Recovery Pet",
                "--pet-notes",
                "a geometric test mascot",
                "--output-dir",
                str(run_dir),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return run_dir

    def manage(
        self,
        run_dir: Path,
        command: str,
        *arguments: str,
        at: int = 0,
        succeeds: bool = True,
    ) -> dict[str, object] | subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [
                sys.executable,
                str(MANAGE),
                "--run-dir",
                str(run_dir),
                "--now",
                timestamp(at),
                command,
                *arguments,
            ],
            capture_output=True,
            text=True,
        )
        if not succeeds:
            return completed
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    def load_manifest(self, run_dir: Path) -> dict[str, object]:
        return json.loads((run_dir / "imagegen-jobs.json").read_text())

    def job(self, manifest: dict[str, object], job_id: str) -> dict[str, object]:
        return next(job for job in manifest["jobs"] if job["id"] == job_id)

    def test_v1_status_is_compatible_and_first_claim_migrates_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_dir = self.prepare_run(Path(temporary_directory))
            manifest_path = run_dir / "imagegen-jobs.json"
            manifest = self.load_manifest(run_dir)
            manifest["schema_version"] = 1
            manifest.pop("retry_policy", None)
            manifest.pop("scheduler", None)
            manifest.pop("revision", None)
            for job in manifest["jobs"]:
                for key in ("attempts", "attempt_count", "max_attempts"):
                    job.pop(key, None)
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

            status = self.manage(run_dir, "status")
            self.assertEqual(2, status["schema_version"])
            self.assertEqual(1, self.load_manifest(run_dir)["schema_version"])

            self.manage(run_dir, "claim", "--job", "base", "--worker-id", "test")
            migrated = self.load_manifest(run_dir)
            self.assertEqual(2, migrated["schema_version"])
            self.assertEqual(1, migrated["migrated_from_schema_version"])
            self.assertEqual("running", self.job(migrated, "base")["status"])

    def test_complete_preserves_result_and_resume_skips_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run_dir = self.prepare_run(root)
            claim = self.manage(
                run_dir,
                "claim",
                "--job",
                "base",
                "--worker-id",
                "test",
            )
            source = root / "generated.png"
            Image.new("RGBA", (64, 64), (30, 80, 120, 255)).save(source)

            self.manage(
                run_dir,
                "complete",
                "--job",
                "base",
                "--claim-token",
                str(claim["claim_token"]),
                "--source",
                str(source),
            )

            self.assertTrue((run_dir / "decoded" / "base.png").is_file())
            self.assertTrue((run_dir / "references" / "canonical-base.png").is_file())
            ready = self.manage(run_dir, "ready")
            self.assertNotIn("base", ready["ready_jobs"])
            self.assertIn("idle", ready["ready_jobs"])

    def test_transport_retry_is_finite_same_prompt_and_degrades_concurrency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_dir = self.prepare_run(Path(temporary_directory))
            original_prompt = "prompts/base-pet.md"
            offsets = (0, 10, 30)
            for attempt_number, offset in enumerate(offsets, start=1):
                claim = self.manage(
                    run_dir,
                    "claim",
                    "--job",
                    "base",
                    "--worker-id",
                    "test",
                    at=offset,
                )
                self.assertEqual(original_prompt, claim["prompt_file"])
                failure = self.manage(
                    run_dir,
                    "fail",
                    "--job",
                    "base",
                    "--claim-token",
                    str(claim["claim_token"]),
                    "--category",
                    "transport",
                    "--code",
                    "http_408",
                    "--message",
                    "Request timed out while reading "
                    + "/"
                    + "Users"
                    + "/synthetic/private.png",
                    at=offset,
                )
                self.assertNotIn(
                    "/" + "Users" + "/",
                    failure["last_error"]["safe_message"],
                )
                expected = "failed_terminal" if attempt_number == 3 else "retry_wait"
                self.assertEqual(expected, failure["status"])
                if attempt_number == 2:
                    self.assertEqual(1, failure["recommended_concurrency"])
                if attempt_number == 1:
                    waiting = self.manage(run_dir, "status", at=offset + 1)
                    base_status = next(
                        job for job in waiting["jobs"] if job["id"] == "base"
                    )
                    self.assertEqual("timeout", base_status["display_status"])
                    retrying = self.manage(run_dir, "status", at=offset + 5)
                    base_status = next(
                        job for job in retrying["jobs"] if job["id"] == "base"
                    )
                    self.assertEqual("retrying", base_status["display_status"])

            manifest = self.load_manifest(run_dir)
            base = self.job(manifest, "base")
            self.assertEqual(3, base["attempt_count"])
            self.assertEqual("failed_terminal", base["status"])
            self.assertEqual([], self.manage(run_dir, "ready", at=60)["ready_jobs"])

    def test_concurrency_limit_is_enforced_before_and_after_degradation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run_dir = self.prepare_run(root)
            base_claim = self.manage(
                run_dir,
                "claim",
                "--job",
                "base",
                "--worker-id",
                "bootstrap",
            )
            base_source = root / "base.png"
            Image.new("RGBA", (64, 64), (20, 70, 110, 255)).save(base_source)
            self.manage(
                run_dir,
                "complete",
                "--job",
                "base",
                "--claim-token",
                str(base_claim["claim_token"]),
                "--source",
                str(base_source),
            )

            initial = self.manage(run_dir, "ready")
            self.assertEqual(3, initial["recommended_concurrency"])
            self.assertEqual(3, initial["available_slots"])
            self.assertEqual(3, len(initial["ready_jobs"]))
            claimed = []
            for job_id in initial["ready_jobs"]:
                claimed.append(
                    self.manage(
                        run_dir,
                        "claim",
                        "--job",
                        str(job_id),
                        "--worker-id",
                        "parallel-worker",
                    )
                )
            saturated = self.manage(run_dir, "ready")
            self.assertEqual(3, saturated["running_jobs"])
            self.assertEqual(0, saturated["available_slots"])
            self.assertEqual([], saturated["ready_jobs"])
            fourth_job = next(
                job["id"]
                for job in self.load_manifest(run_dir)["jobs"]
                if job["status"] == "pending" and job["id"] != "base"
            )
            blocked = self.manage(
                run_dir,
                "claim",
                "--job",
                str(fourth_job),
                "--worker-id",
                "parallel-worker",
                succeeds=False,
            )
            self.assertNotEqual(0, blocked.returncode)
            self.assertIn("concurrency limit reached", blocked.stderr)

            for claimed_job in claimed:
                self.manage(
                    run_dir,
                    "fail",
                    "--job",
                    str(claimed_job["job_id"]),
                    "--claim-token",
                    str(claimed_job["claim_token"]),
                    "--category",
                    "transport",
                    "--code",
                    "http_408",
                    "--message",
                    "request body read timed out",
                )

            degraded = self.manage(run_dir, "ready")
            self.assertEqual(1, degraded["recommended_concurrency"])
            self.assertEqual(1, degraded["available_slots"])
            self.assertEqual(1, len(degraded["ready_jobs"]))
            degraded_claim = self.manage(
                run_dir,
                "claim",
                "--job",
                str(degraded["ready_jobs"][0]),
                "--worker-id",
                "degraded-worker",
            )
            after_claim = self.manage(run_dir, "ready")
            self.assertEqual(1, after_claim["running_jobs"])
            self.assertEqual(0, after_claim["available_slots"])
            self.assertEqual([], after_claim["ready_jobs"])
            another_job = next(
                job["id"]
                for job in self.load_manifest(run_dir)["jobs"]
                if job["status"] == "pending" and job["id"] != degraded_claim["job_id"]
            )
            blocked_degraded = self.manage(
                run_dir,
                "claim",
                "--job",
                str(another_job),
                "--worker-id",
                "degraded-worker",
                succeeds=False,
            )
            self.assertNotEqual(0, blocked_degraded.returncode)
            self.assertIn("concurrency limit reached", blocked_degraded.stderr)

    def test_request_repair_prompt_is_used_once_not_for_transport(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            run_dir = self.prepare_run(root)
            base_claim = self.manage(
                run_dir,
                "claim",
                "--job",
                "base",
                "--worker-id",
                "test",
            )
            base_source = root / "base.png"
            Image.new("RGBA", (64, 64), (50, 80, 110, 255)).save(base_source)
            self.manage(
                run_dir,
                "complete",
                "--job",
                "base",
                "--claim-token",
                str(base_claim["claim_token"]),
                "--source",
                str(base_source),
            )

            first = self.manage(
                run_dir,
                "claim",
                "--job",
                "idle",
                "--worker-id",
                "test",
            )
            self.assertEqual("prompts/rows/idle.md", first["prompt_file"])
            failure = self.manage(
                run_dir,
                "fail",
                "--job",
                "idle",
                "--claim-token",
                str(first["claim_token"]),
                "--category",
                "request",
                "--code",
                "invalid_request",
                "--message",
                "request shape was rejected",
            )
            self.assertEqual("retry_wait", failure["status"])

            repaired = self.manage(
                run_dir,
                "claim",
                "--job",
                "idle",
                "--worker-id",
                "test",
            )
            self.assertEqual(
                "prompts/row-retries/idle.md",
                repaired["prompt_file"],
            )
            transport = self.manage(
                run_dir,
                "fail",
                "--job",
                "idle",
                "--claim-token",
                str(repaired["claim_token"]),
                "--category",
                "transport",
                "--code",
                "http_408",
                "--message",
                "request timed out",
            )
            self.assertEqual("retry_wait", transport["status"])

            same_repair = self.manage(
                run_dir,
                "claim",
                "--job",
                "idle",
                "--worker-id",
                "test",
                at=15,
            )
            self.assertEqual(
                "prompts/row-retries/idle.md",
                same_repair["prompt_file"],
            )
            terminal = self.manage(
                run_dir,
                "fail",
                "--job",
                "idle",
                "--claim-token",
                str(same_repair["claim_token"]),
                "--category",
                "request",
                "--code",
                "invalid_request",
                "--message",
                "request shape was rejected again",
                at=15,
            )
            self.assertEqual("failed_terminal", terminal["status"])

    def test_expired_claim_recovers_on_poll_and_cannot_gain_extra_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_dir = self.prepare_run(Path(temporary_directory))
            first_claim = self.manage(
                run_dir,
                "claim",
                "--job",
                "base",
                "--worker-id",
                "abandoned-worker",
            )
            ready = self.manage(run_dir, "ready", at=1801)
            self.assertEqual(["base"], ready["recovered_expired_claims"])
            self.assertIn("base", ready["ready_jobs"])
            recovered = self.job(self.load_manifest(run_dir), "base")
            self.assertEqual("claim_expired", recovered["last_error"]["code"])
            self.assertEqual(
                "retryable-interruption",
                recovered["attempts"][0]["outcome"],
            )

            for at in (1801, 3602):
                claim = self.manage(
                    run_dir,
                    "claim",
                    "--job",
                    "base",
                    "--worker-id",
                    "abandoned-worker",
                    at=at,
                )
                self.assertNotEqual(first_claim["claim_token"], claim["claim_token"])
                self.manage(run_dir, "status", at=at + 1801)

            terminal = self.job(self.load_manifest(run_dir), "base")
            self.assertEqual(3, terminal["attempt_count"])
            self.assertEqual("failed_terminal", terminal["status"])
            self.assertEqual("terminal-interruption", terminal["attempts"][-1]["outcome"])

    def test_orphan_requires_reconcile_and_reset_is_explicit_recoverable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_dir = self.prepare_run(Path(temporary_directory))
            orphan = run_dir / "decoded" / "base.png"
            Image.new("RGBA", (64, 64), (90, 40, 20, 255)).save(orphan)

            ready = self.manage(run_dir, "ready")
            self.assertNotIn("base", ready["ready_jobs"])
            report = self.manage(run_dir, "reconcile")
            self.assertEqual("orphan_output", report["findings"][0]["code"])
            self.manage(run_dir, "reconcile", "--apply", "--job", "base")
            self.assertEqual("complete", self.job(self.load_manifest(run_dir), "base")["status"])

            reset = self.manage(
                run_dir,
                "reset",
                "--job",
                "base",
                "--reason",
                "operator requested a fresh source",
            )
            self.assertEqual(["base"], reset["reset_jobs"])
            self.assertFalse(orphan.exists())
            self.assertFalse((run_dir / "references" / "canonical-base.png").exists())
            self.assertEqual(2, len(reset["archived_outputs"]))
            for archived in reset["archived_outputs"]:
                self.assertTrue((run_dir / archived).is_file())
            base = self.job(self.load_manifest(run_dir), "base")
            self.assertEqual("pending", base["status"])
            self.assertEqual(0, base["attempt_count"])


if __name__ == "__main__":
    unittest.main()
