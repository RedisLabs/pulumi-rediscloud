#!/usr/bin/env python3
"""Open a pull request when terraform-provider-rediscloud publishes a newer release.

The pin in provider/go.mod is the require line for that module plus the two
comments above it. The require cannot be the v2 tag: the module path has no
/v2 suffix, so Go rejects it. The require stays a pseudo-version of the
release commit. A newer release rewrites only those pin lines. It does not
bump the bridge, Go, or Pulumi, it does not run tfgen, and it does not merge.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

UPSTREAM = "RedisLabs/terraform-provider-rediscloud"
GITHUB_REPO = "RedisLabs/pulumi-rediscloud"
MODULE = "github.com/RedisLabs/terraform-provider-rediscloud"
REPO_NAME = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
TAG_COMMIT = re.compile(
    r"(?m)^[ \t]*// (?P<tag>v\d+\.\d+\.\d+) is commit (?P<commit>[0-9a-f]{40})\.[ \t]*$"
)
REJECT = re.compile(
    r"(?m)^[ \t]*// Go rejects the (?P<tag>v\d+\.\d+\.\d+) tag because that module path has no /v2 suffix\.[ \t]*$"
)
REQUIRE = re.compile(
    rf"(?m)^[ \t]*{re.escape(MODULE)}[ \t]+"
    r"(?P<version>v\d+\.\d+\.\d+-0\.\d{14}-[0-9a-f]{12})[ \t]*$"
)
PSEUDO = re.compile(r"^(?P<prefix>v\d+\.\d+\.\d+-0\.)(?P<ts>\d{14})-(?P<rev>[0-9a-f]{12})$")
GO_VERSION = re.compile(r"(?m)^go[ \t]+(\d+\.\d+(?:\.\d+)?)[ \t]*$")


@dataclass(frozen=True)
class Release:
    tag: str
    commit: str
    committed_at: datetime


@dataclass(frozen=True)
class Pin:
    tag: str
    commit: str
    version: str
    prefix: str
    rev: str


def validate_repo(name: str) -> str:
    if not REPO_NAME.fullmatch(name):
        raise SystemExit(f"invalid GitHub repo: {name}")
    return name


def normalize_tag(tag: str) -> str:
    text = tag.strip()
    if text[:1] in ("v", "V"):
        text = text[1:]
    parts = text.split(".")
    if len(parts) != 3:
        raise SystemExit(f"pre-release tags are not tracked: {tag}")
    for part in parts:
        if not part.isdigit() or (len(part) > 1 and part.startswith("0")):
            raise SystemExit(f"pre-release tags are not tracked: {tag}")
    return f"v{text}"


def version_key(tag: str) -> tuple[int, int, int]:
    normalized = normalize_tag(tag)
    major, minor, patch = normalized[1:].split(".")
    return int(major), int(minor), int(patch)


def parse_github_time(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise SystemExit(f"commit time must include a timezone: {value}")
    return parsed.astimezone(timezone.utc)


def read_pin(text: str) -> Pin:
    comments = list(TAG_COMMIT.finditer(text))
    rejects = list(REJECT.finditer(text))
    requires = list(REQUIRE.finditer(text))
    if len(comments) != 1 or len(rejects) != 1 or len(requires) != 1:
        raise SystemExit(
            "expected one Terraform pin comment, one Go-rejection comment, "
            f"and one {MODULE} require"
        )
    tag = comments[0].group("tag")
    commit = comments[0].group("commit")
    if rejects[0].group("tag") != tag:
        raise SystemExit("Terraform pin comments name different tags")
    version = requires[0].group("version")
    matched = PSEUDO.fullmatch(version)
    if matched is None:
        raise SystemExit(f"Terraform require is not a pseudo-version: {version}")
    rev = matched.group("rev")
    if not commit.startswith(rev):
        raise SystemExit("Terraform pin comment does not match the require commit")
    return Pin(
        tag=tag,
        commit=commit,
        version=version,
        prefix=matched.group("prefix"),
        rev=rev,
    )


def module_version(text: str, module: str) -> str:
    found = re.findall(
        rf"(?m)^[ \t]*{re.escape(module)}[ \t]+(v\S+)",
        text,
    )
    if len(found) != 1:
        raise SystemExit(f"expected one require for {module}, found {len(found)}")
    return found[0]


def protected_versions(text: str) -> dict[str, str]:
    go = GO_VERSION.findall(text)
    if len(go) != 1:
        raise SystemExit(f"expected one go version, found {len(go)}")
    return {
        "go": go[0],
        "bridge": module_version(text, "github.com/pulumi/pulumi-terraform-bridge/v3"),
        "pulumi": module_version(text, "github.com/pulumi/pulumi/pkg/v3"),
        "sdk": module_version(text, "github.com/pulumi/pulumi/sdk/v3"),
    }


def pseudo_version(pin: Pin, release: Release) -> str:
    if len(release.commit) != 40 or any(char not in "0123456789abcdef" for char in release.commit):
        raise SystemExit("release commit must be 40 hex characters")
    timestamp = release.committed_at.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{pin.prefix}{timestamp}-{release.commit[:12]}"


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"expected one occurrence of {old!r}, found {text.count(old)}")
    return text.replace(old, new, 1)


def assert_only_pin_changed(before: str, after: str) -> None:
    old_lines = before.splitlines()
    new_lines = after.splitlines()
    if len(old_lines) != len(new_lines):
        raise SystemExit("pin update changed the number of lines in provider/go.mod")
    for old, new in zip(old_lines, new_lines):
        if old == new:
            continue
        if REQUIRE.search(old) and REQUIRE.search(new):
            continue
        if TAG_COMMIT.search(old) and TAG_COMMIT.search(new):
            continue
        if REJECT.search(old) and REJECT.search(new):
            continue
        raise SystemExit("pin update changed a line that is not the Terraform pin")
    if protected_versions(before) != protected_versions(after):
        raise SystemExit("pin update changed the bridge, Go, or Pulumi version")


def apply_pin(text: str, release: Release) -> str:
    pin = read_pin(text)
    release = Release(
        tag=normalize_tag(release.tag),
        commit=release.commit,
        committed_at=release.committed_at,
    )
    if release.commit.startswith(pin.rev) or version_key(release.tag) <= version_key(pin.tag):
        return text
    version = pseudo_version(pin, release)
    updated = replace_once(
        text,
        f"// {pin.tag} is commit {pin.commit}.",
        f"// {release.tag} is commit {release.commit}.",
    )
    updated = replace_once(
        updated,
        f"// Go rejects the {pin.tag} tag because that module path has no /v2 suffix.",
        f"// Go rejects the {release.tag} tag because that module path has no /v2 suffix.",
    )
    updated = replace_once(
        updated,
        f"{MODULE} {pin.version}",
        f"{MODULE} {version}",
    )
    assert_only_pin_changed(text, updated)
    if read_pin(updated).version == pin.version:
        raise SystemExit("Terraform require was not updated")
    return updated


def github_request(url: str, opener) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "pulumi-rediscloud",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with opener(request, timeout=30) as response:
            payload = json.load(response)
    except SystemExit:
        raise
    except Exception as exc:
        raise SystemExit(f"failed to read the Terraform provider release: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("GitHub release response was not an object")
    return payload


def fetch_release(upstream: str, tag: str = "", opener=urllib.request.urlopen) -> Release:
    repo = validate_repo(upstream)
    selected = tag.strip()
    if not selected:
        latest = github_request(
            f"https://api.github.com/repos/{repo}/releases/latest",
            opener,
        )
        if "tag_name" not in latest:
            raise SystemExit("latest Terraform provider release has no tag")
        selected = str(latest["tag_name"])
    selected = normalize_tag(selected)
    commit = github_request(
        f"https://api.github.com/repos/{repo}/commits/{selected}",
        opener,
    )
    sha = str(commit.get("sha", ""))
    try:
        committed = commit["commit"]["committer"]["date"]
    except (KeyError, TypeError) as exc:
        raise SystemExit("Terraform provider commit has no committer time") from exc
    return Release(tag=selected, commit=sha, committed_at=parse_github_time(str(committed)))


def run(args: list[str], cwd: Path | None = None) -> str:
    completed = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise SystemExit(f"{args[0]} failed: {detail}")
    return completed.stdout


def write_temp(name: str, content: str) -> str:
    handle = tempfile.NamedTemporaryFile(
        "w",
        prefix=f"track-terraform-{name}-",
        suffix=".txt",
        delete=False,
    )
    with handle:
        handle.write(content)
    return handle.name


def pull_request_body(pin: Pin, release: Release) -> str:
    return "\n".join(
        [
            "This pull request was opened by `.github/workflows/terraform-release.yaml`.",
            "",
            f"`RedisLabs/terraform-provider-rediscloud` published {release.tag}, which is newer than the pin {pin.tag}.",
            "This changes only the Terraform provider pin in `provider/go.mod`.",
            "Go cannot require the v2 tag because the module path has no /v2 suffix, so the require stays a pseudo-version of the release commit.",
            "",
            "A person regenerates and reviews.",
            "This workflow does not run tfgen, does not bump the bridge, Go, or Pulumi, and does not merge.",
            "",
        ]
    )


def commit_message(pin: Pin, release: Release) -> str:
    return "\n".join(
        [
            f"Track Terraform provider {release.tag}.",
            "",
            f"The pin moves from {pin.tag} to {release.tag}. A person regenerates and reviews. This does not merge.",
            "",
        ]
    )


def existing_pull_request(root: Path, github_repo: str, branch: str) -> bool:
    listed = json.loads(
        run(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                github_repo,
                "--head",
                branch,
                "--state",
                "open",
                "--json",
                "number",
            ],
            root,
        )
        or "[]"
    )
    return bool(listed)


def remote_branch_sha(root: Path, branch: str) -> str | None:
    listed = run(
        ["git", "-C", str(root), "ls-remote", "origin", f"refs/heads/{branch}"]
    ).strip()
    if not listed:
        return None
    sha = listed.split()[0]
    if len(sha) < 7:
        raise SystemExit(f"unexpected ls-remote output: {listed}")
    return sha


def create_pull_request(
    root: Path,
    github_repo: str,
    base: str,
    branch: str,
    pin: Pin,
    release: Release,
) -> str:
    body = write_temp("body", pull_request_body(pin, release))
    try:
        return run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                github_repo,
                "--base",
                base,
                "--head",
                branch,
                "--title",
                f"Track Terraform provider {release.tag}",
                "--body-file",
                body,
            ],
            root,
        ).strip()
    finally:
        os.unlink(body)


def open_pull_request(
    root: Path,
    before: str,
    after: str,
    release: Release,
    github_repo: str,
) -> str:
    root = root.resolve()
    github_repo = validate_repo(github_repo)
    pin = read_pin(before)
    desired = read_pin(after)
    branch = f"track/terraform-provider-{release.tag}"
    if existing_pull_request(root, github_repo, branch):
        print(f"decision=already-open pin={pin.tag} candidate={release.tag}")
        return "already-open"
    base = run(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"]).strip()
    if base in ("", "HEAD"):
        raise SystemExit("refusing to open a pull request from a detached HEAD")
    remote = remote_branch_sha(root, branch)
    if remote:
        run(["git", "-C", str(root), "fetch", "origin", f"refs/heads/{branch}"])
        remote_pin = read_pin(
            run(["git", "-C", str(root), "show", "FETCH_HEAD:provider/go.mod"])
        )
        if remote_pin.version != desired.version:
            raise SystemExit(
                f"remote branch {branch} exists with a different pin; not replacing it"
            )
        url = create_pull_request(root, github_repo, base, branch, pin, release)
        print(f"decision=retried pin={pin.tag} candidate={release.tag} url={url}")
        return url

    gomod = root / "provider" / "go.mod"
    gomod.write_text(after)
    run(["git", "-C", str(root), "checkout", "-B", branch])
    run(["git", "-C", str(root), "add", "--", "provider/go.mod"])
    message = write_temp("commit", commit_message(pin, release))
    try:
        run(
            [
                "git",
                "-C",
                str(root),
                "-c",
                "user.email=41898282+github-actions[bot]@users.noreply.github.com",
                "-c",
                "user.name=github-actions[bot]",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-F",
                message,
            ]
        )
    finally:
        os.unlink(message)
    run(["git", "-C", str(root), "push", "--set-upstream", "origin", branch])
    url = create_pull_request(root, github_repo, base, branch, pin, release)
    print(f"decision=opened pin={pin.tag} candidate={release.tag} url={url}")
    return url


def main(argv: list[str] | None = None, *, fetch=None, open_pr=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--upstream", default=UPSTREAM)
    parser.add_argument(
        "--github-repo",
        default=os.environ.get("GITHUB_REPOSITORY", GITHUB_REPO),
    )
    parser.add_argument("--tag", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not args.tag:
        args.tag = os.environ.get("TRACK_TAG", "")
    if os.environ.get("TRACK_DRY_RUN", "").lower() == "true":
        args.dry_run = True
    if fetch is None:
        fetch = fetch_release
    if open_pr is None:
        open_pr = open_pull_request

    root = Path(args.repo_root)
    gomod = root / "provider" / "go.mod"
    before = gomod.read_text()
    pin = read_pin(before)
    release = fetch(args.upstream, args.tag)
    after = apply_pin(before, release)
    if after == before:
        print(f"decision=none pin={pin.tag} candidate={normalize_tag(release.tag)}")
        return 0
    if args.dry_run:
        print(f"decision=would-open pin={pin.tag} candidate={normalize_tag(release.tag)}")
        return 0
    open_pr(root, before, after, release, args.github_repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
