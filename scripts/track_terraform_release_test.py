#!/usr/bin/env python3
"""Hermetic tests for Terraform provider release tracking.

These tests do not use the network and do not call the Cloud API.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

import track_terraform_release as track

REPO = Path(__file__).resolve().parents[1]
CURRENT = track.Release(
    tag="v2.19.3",
    commit="ca1e97245378dc8e4be6413cf1745ef6805dc66d",
    committed_at=datetime(2026, 10, 28, 13, 9, 56, tzinfo=timezone.utc),
)
NEWER = track.Release(
    tag="v2.20.0",
    commit="0123456789abcdef0123456789abcdef01234567",
    committed_at=datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc),
)


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=True,
    )


def init_repo(repo: Path, gomod: str) -> None:
    provider = repo / "provider"
    provider.mkdir()
    (provider / "go.mod").write_text(gomod)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "add", "--", "provider/go.mod")
    git(repo, "commit", "-m", "initial")
    bare = repo.parent / "origin.git"
    subprocess.run(
        ["git", "init", "--bare", "-b", "main", str(bare)],
        check=True,
        capture_output=True,
    )
    git(repo, "remote", "add", "origin", str(bare))
    git(repo, "push", "origin", "main")


class GhLog:
    def __init__(self) -> None:
        self.calls: list[dict] = []


@contextmanager
def fake_gh():
    holder = GhLog()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        log = root / "gh.log"
        script = root / "gh"
        script.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env python3",
                    "import json, os, sys",
                    "record = {'argv': sys.argv[1:]}",
                    "if '--body-file' in sys.argv:",
                    "    body_path = sys.argv[sys.argv.index('--body-file') + 1]",
                    "    record['body'] = open(body_path, encoding='utf-8').read()",
                    "if 'merge' in sys.argv:",
                    "    sys.stderr.write('merge is not allowed\\n')",
                    "    raise SystemExit(2)",
                    "with open(os.environ['GH_LOG'], 'a', encoding='utf-8') as handle:",
                    "    json.dump(record, handle)",
                    "    handle.write('\\n')",
                    "if sys.argv[1:3] == ['pr', 'list']:",
                    "    sys.stdout.write('[]')",
                    "    raise SystemExit(0)",
                    "if sys.argv[1:3] == ['pr', 'create']:",
                    "    sys.stdout.write('https://example.test/pull/1\\n')",
                    "    raise SystemExit(0)",
                    "sys.stderr.write('unexpected gh command\\n')",
                    "raise SystemExit(1)",
                    "",
                ]
            )
        )
        script.chmod(0o755)
        old_path = os.environ.get("PATH", "")
        old_log = os.environ.get("GH_LOG")
        os.environ["PATH"] = str(root) + os.pathsep + old_path
        os.environ["GH_LOG"] = str(log)
        try:
            yield holder
        finally:
            if log.exists():
                holder.calls = [
                    json.loads(line) for line in log.read_text().splitlines() if line
                ]
            os.environ["PATH"] = old_path
            if old_log is None:
                os.environ.pop("GH_LOG", None)
            else:
                os.environ["GH_LOG"] = old_log


class TrackTerraformReleaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = {
            name: os.environ.get(name)
            for name in (
                "TRACK_TAG",
                "TRACK_DRY_RUN",
                "TRACK_CANDIDATE",
                "TRACK_BUNDLE",
                "TRACK_REUSE",
                "GH_TOKEN",
                "RUNNER_TEMP",
            )
        }
        for name in self._saved:
            os.environ.pop(name, None)
        self.original = (REPO / "provider" / "go.mod").read_text()

    def tearDown(self) -> None:
        for name, value in self._saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        self.assertEqual((REPO / "provider" / "go.mod").read_text(), self.original)

    def test_same_pin_opens_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            provider = root / "provider"
            provider.mkdir()
            (provider / "go.mod").write_text(self.original)
            opened: list[object] = []
            output = io.StringIO()
            with redirect_stdout(output):
                code = track.main(
                    ["--repo-root", str(root)],
                    fetch=lambda upstream, tag: CURRENT,
                    open_pr=lambda *args, **kwargs: opened.append((args, kwargs)),
                )
            self.assertEqual(code, 0)
            self.assertEqual(opened, [])
            self.assertEqual((provider / "go.mod").read_text(), self.original)
            self.assertIn("decision=none pin=v2.19.3 candidate=v2.19.3", output.getvalue())

    def test_newer_tag_changes_only_the_pin(self) -> None:
        updated = track.apply_pin(self.original, NEWER)
        changed = [
            (old, new)
            for old, new in zip(self.original.splitlines(), updated.splitlines())
            if old != new
        ]
        self.assertEqual(
            changed,
            [
                (
                    "\t// v2.19.3 is commit ca1e97245378dc8e4be6413cf1745ef6805dc66d.",
                    "\t// v2.20.0 is commit 0123456789abcdef0123456789abcdef01234567.",
                ),
                (
                    "\t// Go rejects the v2.19.3 tag because that module path has no /v2 suffix.",
                    "\t// Go rejects the v2.20.0 tag because that module path has no /v2 suffix.",
                ),
                (
                    "\tgithub.com/RedisLabs/terraform-provider-rediscloud v1.9.1-0.20261028130956-ca1e97245378",
                    "\tgithub.com/RedisLabs/terraform-provider-rediscloud v1.9.1-0.20261101120000-0123456789ab",
                ),
            ],
        )
        self.assertEqual(
            track.protected_versions(self.original),
            track.protected_versions(updated),
        )
        self.assertNotIn("terraform-provider-rediscloud v2.", updated)

        def generate(root: Path) -> None:
            if "GH_TOKEN" in os.environ or "GITHUB_TOKEN" in os.environ:
                raise SystemExit("token was visible to generate")
            schema = root / "provider/cmd/pulumi-resource-rediscloud/schema.json"
            schema.parent.mkdir(parents=True)
            schema.write_text("{}\n")
            sdk = root / "sdk/go/rediscloud/doc.go"
            sdk.parent.mkdir(parents=True)
            sdk.write_text("package rediscloud\n")

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            init_repo(repo, self.original)
            output = io.StringIO()
            bundle_dir = Path(tmp) / "runner"
            bundle_dir.mkdir()
            os.environ["GH_TOKEN"] = "token-sentinel"
            os.environ["RUNNER_TEMP"] = str(bundle_dir)
            with fake_gh() as log, redirect_stdout(output):
                code = track.main(
                    ["--repo-root", str(repo), "--github-repo", "local/test", "--prepare-only"],
                    fetch=lambda upstream, tag: NEWER,
                    generate=generate,
                )
                self.assertEqual(code, 0)
                self.assertIn("decision=prepared", output.getvalue())
                self.assertNotIn("token-sentinel", output.getvalue())
                names = set(git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").stdout.split())
                self.assertIn("provider/go.mod", names)
                self.assertIn("provider/cmd/pulumi-resource-rediscloud/schema.json", names)
                self.assertIn("sdk/go/rediscloud/doc.go", names)
                committed = git(repo, "show", "HEAD:provider/go.mod").stdout
                self.assertEqual(committed, updated)
                parent = git(repo, "show", "HEAD^:provider/go.mod").stdout
                self.assertEqual(parent, self.original)
                remote = git(repo, "ls-remote", "origin", "refs/heads/track/terraform-provider-v2.20.0").stdout
                self.assertEqual(remote, "")
                os.environ["TRACK_CANDIDATE"] = "v2.20.0"
                os.environ["TRACK_BUNDLE"] = str(bundle_dir / "track-release.bundle")
                git(repo, "checkout", "main")
                code = track.main(
                    ["--repo-root", str(repo), "--github-repo", "local/test", "--publish-only"],
                )
            self.assertEqual(code, 0)
            self.assertIn("decision=opened", output.getvalue())
            self.assertIn("https://example.test/pull/1", output.getvalue())
            commands = [call["argv"][:2] for call in log.calls]
            self.assertEqual(commands, [["pr", "list"], ["pr", "create"]])
            self.assertNotIn("merge", log.calls[1]["argv"])
            self.assertIn("make tfgen", log.calls[1]["body"])
            self.assertIn("does not merge", log.calls[1]["body"])
            self.assertNotIn("token-sentinel", log.calls[1]["body"])

    def test_workflow_runs_on_schedule_and_dispatch_only(self) -> None:
        text = (REPO / ".github/workflows/terraform-release.yaml").read_text()
        self.assertIn("schedule:", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("--prepare-only", text)
        self.assertIn("--publish-only", text)
        self.assertIn("go mod tidy", text)
        self.assertNotIn("pull_request", text)
        self.assertNotIn("pr merge", text)
        script = (REPO / "scripts/track_terraform_release.py").read_text()
        self.assertIn('"tfgen"', script)
        self.assertIn('"build_go"', script)
        self.assertIn("without_github_tokens", script)

    def test_fetch_uses_the_tag_commit_not_the_branch_name(self) -> None:
        urls: list[str] = []

        class Response:
            def __init__(self, payload: dict) -> None:
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self) -> bytes:
                return json.dumps(self.payload).encode()

        def opener(request, timeout):
            self.assertEqual(timeout, 30)
            urls.append(request.full_url)
            if request.full_url.endswith("/releases/latest"):
                return Response({"tag_name": "v2.19.3", "target_commitish": "main"})
            if request.full_url.endswith("/commits/v2.19.3"):
                return Response(
                    {
                        "sha": CURRENT.commit,
                        "commit": {"committer": {"date": "2026-10-28T13:09:56Z"}},
                    }
                )
            raise AssertionError(request.full_url)

        release = track.fetch_release(track.UPSTREAM, "", opener)
        self.assertEqual(release, CURRENT)
        self.assertNotIn("main", urls[-1])


if __name__ == "__main__":
    unittest.main()
