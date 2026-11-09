#!/usr/bin/env python3
"""Nightly QA acceptance for one ACL rule, one Pro subscription, and one database.

The Pulumi program in examples/qa creates the resources. This wrapper refuses a
missing or production REDISCLOUD_URL, deletes leftover pulumi-ci- subscriptions
before create, picks a deployment CIDR, destroys on a failed database step, and
checks HTTP 404 after destroy. Hermetic tests point the HTTP client at a fake
server. This script does not call Redis Cloud unless a person runs it with a
non-production URL.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PREFIX = "pulumi-ci-"
REFUSED_HOST = "api.redislabs.com"
OUTPUT_NAMES = ("publicEndpoint", "privateEndpoint")
SECRET_FIELDS = {
    "paymentMethodId",
    "publicEndpoint",
    "privateEndpoint",
    "password",
    "apiKey",
    "secretKey",
    "api_key",
    "secret_key",
}
RUN_ID = re.compile(r"[A-Za-z0-9_-]+")
RESOURCE_ID = re.compile(r"[0-9]+")
REPO = Path(__file__).resolve().parents[1]
PROGRAM_DIR = REPO / "examples" / "qa"


class SuiteFailure(Exception):
    """The QA suite cannot continue. The message must not contain secrets."""


class Log:
    def __init__(self, secrets: list[str] | None = None) -> None:
        self.lines: list[str] = []
        self.secrets = [item for item in (secrets or []) if item]

    def absorb(self, value: object) -> None:
        found: list[str] = []
        _collect_secrets(value, found)
        for item in found:
            if item and item not in self.secrets:
                self.secrets.append(item)

    def __call__(self, message: str) -> None:
        text = str(message)
        for secret in self.secrets:
            text = text.replace(secret, "[redacted]")
        self.lines.append(text)
        print(text, flush=True)


def _collect_secrets(value: object, found: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in SECRET_FIELDS and item not in (None, ""):
                found.append(str(item))
            _collect_secrets(item, found)
    elif isinstance(value, list):
        for item in value:
            _collect_secrets(item, found)


def refuse_url(url: str | None) -> str:
    """Return the API base URL, or refuse before any create or HTTP call."""
    text = "" if url is None else str(url).strip()
    if not text:
        raise SuiteFailure("REDISCLOUD_URL is empty")
    parsed = urllib.parse.urlsplit(text)
    host = (parsed.hostname or "").rstrip(".").lower()
    if parsed.scheme.lower() != "https" or not host:
        raise SuiteFailure("REDISCLOUD_URL is not HTTPS")
    if host == REFUSED_HOST or host.endswith("." + REFUSED_HOST):
        raise SuiteFailure("REDISCLOUD_URL host is refused")
    return text.rstrip("/")


def choose_cidr(used: set[str]) -> str:
    """Pick a /24 that is not already a deployment CIDR on the account."""
    for second in range(256):
        for third in range(256):
            cidr = f"10.{second}.{third}.0/24"
            if cidr not in used:
                return cidr
    raise SuiteFailure("no free deployment CIDR")


def deployment_cidrs(subscriptions: list) -> set[str]:
    found: set[str] = set()
    for sub in subscriptions:
        if not isinstance(sub, dict):
            continue
        for detail in sub.get("cloudDetails") or []:
            if not isinstance(detail, dict):
                continue
            for region in detail.get("regions") or []:
                if not isinstance(region, dict):
                    continue
                for net in region.get("networking") or []:
                    if not isinstance(net, dict):
                        continue
                    cidr = net.get("deploymentCIDR") or net.get("deploymentCidr")
                    if cidr:
                        found.add(str(cidr))
    return found


def prefixed(subscriptions: list) -> list:
    rows = []
    for sub in subscriptions:
        if not isinstance(sub, dict):
            continue
        if str(sub.get("name") or "").startswith(PREFIX):
            rows.append(sub)
    return rows


def subscription_rows(body: object) -> list:
    if isinstance(body, dict):
        rows = body.get("subscriptions") or []
        return list(rows) if isinstance(rows, list) else []
    if isinstance(body, list):
        return body
    return []


def database_rows(body: object) -> list:
    if not isinstance(body, dict):
        return []
    rows = []
    for sub in body.get("subscription") or []:
        if isinstance(sub, dict):
            databases = sub.get("databases") or []
            if isinstance(databases, list):
                rows.extend(databases)
    return rows


def safe_resource_id(value: object) -> str:
    text = str(value).strip()
    if not RESOURCE_ID.fullmatch(text):
        raise SuiteFailure("resource id is not safe to place in a path")
    return text


def safe_run_id(value: str) -> str:
    text = str(value).strip()
    if not RUN_ID.fullmatch(text):
        raise SuiteFailure("run id is not safe")
    return text


def map_secret(raw: str) -> dict[str, str]:
    """Map the REDISCLOUD_QA JSON object onto the provider environment names."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SuiteFailure("REDISCLOUD_QA is not JSON") from exc
    if not isinstance(data, dict):
        raise SuiteFailure("REDISCLOUD_QA is not a JSON object")
    api_key = str(data.get("api_key") or "").strip()
    secret_key = str(data.get("secret_key") or "").strip()
    url = str(data.get("url") or "").strip()
    if not api_key or not secret_key:
        raise SuiteFailure("REDISCLOUD_QA is missing api_key or secret_key")
    if any("\n" in item or "\r" in item for item in (api_key, secret_key, url)):
        raise SuiteFailure("REDISCLOUD_QA values must be single-line")
    return {
        "REDISCLOUD_ACCESS_KEY": api_key,
        "REDISCLOUD_SECRET_KEY": secret_key,
        "REDISCLOUD_URL": url,
    }


class HttpCloud:
    """HTTP client for list, status, cleanup, and 404 checks. It does not create resources."""

    def __init__(self, url: str | None, api_key: str, secret_key: str, log: Log, opener=None) -> None:
        self.url = url
        self.api_key = api_key
        self.secret_key = secret_key
        self.log = log
        self.opener = opener or urllib.request.urlopen

    def list_subscriptions(self) -> list:
        code, body = self._json("GET", "/subscriptions")
        self.log(f"list subscriptions HTTP {code}")
        if code != 200:
            raise SuiteFailure(f"list subscriptions HTTP {code}")
        self.log.absorb(body)
        return subscription_rows(body)

    def subscription_status(self, subscription_id: str) -> tuple[int, str]:
        code, body = self._json("GET", f"/subscriptions/{safe_resource_id(subscription_id)}")
        self.log.absorb(body)
        status = ""
        if isinstance(body, dict):
            status = str(body.get("status") or "")
        return code, status

    def database_status(self, subscription_id: str, database_id: str) -> tuple[int, str]:
        path = (
            f"/subscriptions/{safe_resource_id(subscription_id)}"
            f"/databases/{safe_resource_id(database_id)}"
        )
        code, body = self._json("GET", path)
        self.log.absorb(body)
        status = ""
        if isinstance(body, dict):
            status = str(body.get("status") or "")
        return code, status

    def get_subscription(self, subscription_id: str) -> int:
        code, body = self._json("GET", f"/subscriptions/{safe_resource_id(subscription_id)}")
        self.log.absorb(body)
        return code

    def get_database(self, subscription_id: str, database_id: str) -> int:
        path = (
            f"/subscriptions/{safe_resource_id(subscription_id)}"
            f"/databases/{safe_resource_id(database_id)}"
        )
        code, body = self._json("GET", path)
        self.log.absorb(body)
        return code

    def delete_run_subscription(self, subscription_id: str) -> None:
        sub_id = safe_resource_id(subscription_id)
        code, body = self._json("GET", f"/subscriptions/{sub_id}/databases?limit=100&offset=0")
        self.log(f"list databases HTTP {code}")
        self.log.absorb(body)
        if code == 200:
            for row in database_rows(body):
                if not isinstance(row, dict) or row.get("databaseId") in (None, ""):
                    continue
                db_id = safe_resource_id(row.get("databaseId"))
                deleted, _ = self._json("DELETE", f"/subscriptions/{sub_id}/databases/{db_id}")
                self.log(f"cleanup database HTTP {deleted}")
        elif code != 404:
            raise SuiteFailure(f"list databases HTTP {code}")
        deleted, _ = self._json("DELETE", f"/subscriptions/{sub_id}")
        self.log(f"cleanup subscription HTTP {deleted}")

    def _json(self, method: str, path: str) -> tuple[int, object]:
        code, raw = self._request(method, path)
        if not raw:
            return code, None
        try:
            return code, json.loads(raw.decode())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SuiteFailure(f"{method} response is not JSON") from exc

    def _request(self, method: str, path: str) -> tuple[int, bytes]:
        base = refuse_url(self.url)
        if not path.startswith("/"):
            raise SuiteFailure("cloud path must be absolute")
        target = base + path
        request = urllib.request.Request(target, method=method)
        request.add_header("Accept", "application/json")
        request.add_header("X-Api-Key", self.api_key)
        request.add_header("X-Api-Secret-Key", self.secret_key)
        try:
            response = self.opener(request, timeout=60)
        except urllib.error.HTTPError as exc:
            try:
                return exc.code, exc.read()
            finally:
                exc.close()
        except urllib.error.URLError as exc:
            raise SuiteFailure("cloud request failed") from exc
        try:
            return response.status, response.read()
        finally:
            response.close()


class LiveProgram:
    """Run examples/qa. The program creates the ACL rule, subscription, and database."""

    def __init__(self, env: dict[str, str], log: Log) -> None:
        self.env = env
        self.log = log
        self._name = ""
        self._cidr = ""
        self._outputs: dict = {}

    def create_subscription(self, name: str, cidr: str) -> str:
        self._name = name
        self._cidr = cidr
        self._ensure_stack()
        self._config(include_database=False)
        self._pulumi(["up", "--yes", "--skip-preview"])
        outputs = self._read_outputs()
        if "subscriptionId" not in outputs:
            raise SuiteFailure("subscription output subscriptionId is missing")
        return str(outputs["subscriptionId"])

    def create_database(self, name: str, subscription_id: str) -> str:
        del subscription_id  # the program reads subscription.ID(), not this argument
        self._name = name
        self._config(include_database=True)
        self._pulumi(["up", "--yes", "--skip-preview"])
        outputs = self._read_outputs()
        if "databaseId" not in outputs:
            raise SuiteFailure("database output databaseId is missing")
        return str(outputs["databaseId"])

    def output_names(self) -> list[str]:
        return sorted(self._read_outputs())

    def delete_subscription(self, subscription_id: str) -> None:
        del subscription_id
        self._pulumi(["destroy", "--yes", "--skip-preview"])

    def destroy(self) -> None:
        self._pulumi(["destroy", "--yes", "--skip-preview"])

    def _ensure_stack(self) -> None:
        select = self._pulumi(["stack", "select", "qa", "--create"], check=False)
        if select != 0:
            self._pulumi(["stack", "init", "qa", "--non-interactive"])

    def _config(self, include_database: bool) -> None:
        flag = "true" if include_database else "false"
        self._pulumi(["config", "set", "name", self._name])
        self._pulumi(["config", "set", "cidr", self._cidr])
        self._pulumi(["config", "set", "cloudProvider", self.env.get("QA_CLOUD_PROVIDER", "AWS")])
        self._pulumi(["config", "set", "region", self.env.get("QA_REGION", "us-east-1")])
        self._pulumi(["config", "set", "includeDatabase", flag])

    def _read_outputs(self) -> dict:
        completed = self._run(["stack", "output", "--json"])
        try:
            data = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise SuiteFailure("pulumi stack output is not JSON") from exc
        if not isinstance(data, dict):
            raise SuiteFailure("pulumi stack output is not an object")
        self.log.absorb(data)
        self._outputs = data
        return data

    def _pulumi(self, args: list[str], check: bool = True) -> int:
        completed = self._run(args)
        self.log(f"pulumi {args[0]} exit {completed.returncode}")
        if check and completed.returncode != 0:
            raise SuiteFailure(f"pulumi {args[0]} exit {completed.returncode}")
        return completed.returncode

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["pulumi", *args],
            cwd=PROGRAM_DIR,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )


class Deps:
    def __init__(
        self,
        url: str | None,
        run_id: str,
        cloud: HttpCloud,
        program,
        log: Log,
        sleep=time.sleep,
        now=time.monotonic,
        cloud_provider: str = "AWS",
        region: str = "us-east-1",
        evidence_hold_seconds: int = 0,
    ) -> None:
        self.url = url
        self.run_id = run_id
        self.cloud = cloud
        self.program = program
        self.log = log
        self.sleep = sleep
        self.now = now
        self.cloud_provider = cloud_provider
        self.region = region
        self.evidence_hold_seconds = evidence_hold_seconds
        self.poll = 30.0
        self.timeouts = {
            "subscription": 2700.0,
            "database": 1800.0,
            "delete": 900.0,
        }


def clear_leftovers(deps: Deps) -> None:
    """Delete leftover pulumi-ci- subscriptions and wait until they are gone.

    A crashed runner used to leave a pulumi-ci- name that made every later
    run refuse to create. Names that do not start with pulumi-ci- are left
    alone. cleanup_only still deletes only this run.
    """
    leftovers = prefixed(deps.cloud.list_subscriptions())
    if not leftovers:
        return
    deps.log(f"deleting {len(leftovers)} leftover pulumi-ci- subscription(s)")
    for sub in leftovers:
        if sub.get("id") in (None, ""):
            raise SuiteFailure("leftover pulumi-ci- subscription has no id")
        deps.cloud.delete_run_subscription(str(sub.get("id")))
    deadline = deps.now() + deps.timeouts["delete"]
    while prefixed(deps.cloud.list_subscriptions()):
        if deps.now() >= deadline:
            deps.log("pulumi-ci- subscription still present; refusing to create")
            raise SuiteFailure("pulumi-ci- subscription still present")
        deps.sleep(deps.poll)


def run_acceptance(deps: Deps) -> None:
    """Create and delete this run. Clear leftover pulumi-ci- names first."""
    refuse_url(deps.url)
    run_id = safe_run_id(deps.run_id)
    clear_leftovers(deps)
    subscriptions = deps.cloud.list_subscriptions()

    cidr = choose_cidr(deployment_cidrs(subscriptions))
    deps.log(f"cidr {cidr}")
    name = f"{PREFIX}{run_id}"
    deps.log(f"target cloud {deps.cloud_provider} region {deps.region} name {name}")
    created = None
    destroyed = False
    try:
        created = str(deps.program.create_subscription(name, cidr))
        _wait_active(
            deps,
            "subscription",
            lambda: deps.cloud.subscription_status(created),
        )
        try:
            database_id = str(deps.program.create_database(name, created))
        except Exception:
            deps.program.delete_subscription(created)
            destroyed = True
            deps.log("database step failed; subscription delete requested")
            raise
        _wait_active(
            deps,
            "database",
            lambda: deps.cloud.database_status(created, database_id),
        )
        names = list(deps.program.output_names())
        deps.log("output names " + ",".join(names))
        missing = [item for item in OUTPUT_NAMES if item not in names]
        if missing:
            raise SuiteFailure("missing output name " + ",".join(missing))
        deps.log(
            f"active evidence checkpoint subscription {created} database {database_id} "
            f"cloud {deps.cloud_provider} region {deps.region}"
        )
        if deps.evidence_hold_seconds > 0:
            deps.log(f"evidence hold {deps.evidence_hold_seconds} seconds")
            deps.sleep(float(deps.evidence_hold_seconds))
        deps.program.destroy()
        destroyed = True
        database_code = _wait_http(deps, "database", lambda: deps.cloud.get_database(created, database_id))
        subscription_code = _wait_http(deps, "subscription", lambda: deps.cloud.get_subscription(created))
        if database_code != 404 or subscription_code != 404:
            raise SuiteFailure("delete did not return HTTP 404")
        deps.log("qa live ok")
    except Exception:
        if created is not None and not destroyed:
            deps.program.delete_subscription(created)
            deps.log("subscription delete requested")
        raise


def cleanup_only(deps: Deps) -> None:
    """Delete the subscription this run created. Leave any other pulumi-ci- name alone."""
    refuse_url(deps.url)
    run_id = safe_run_id(deps.run_id)
    name = f"{PREFIX}{run_id}"
    matches = []
    for sub in deps.cloud.list_subscriptions():
        if isinstance(sub, dict) and str(sub.get("name") or "") == name:
            matches.append(sub)
    if not matches:
        deps.log("cleanup found no subscription for this run")
        return
    for sub in matches:
        deps.cloud.delete_run_subscription(str(sub.get("id")))
    deps.log("cleanup deleted this run")


def _wait_active(deps: Deps, label: str, fetch) -> None:
    deadline = deps.now() + deps.timeouts[label]
    while True:
        code, status = fetch()
        deps.log(f"{label} HTTP {code} status {status}")
        if code == 404:
            raise SuiteFailure(f"{label} HTTP 404")
        if status == "active" and code == 200:
            return
        if deps.now() >= deadline:
            raise SuiteFailure(f"{label} did not become active")
        deps.sleep(deps.poll)


def _wait_http(deps: Deps, label: str, fetch) -> int:
    deadline = deps.now() + deps.timeouts["delete"]
    code = 0
    while True:
        code = fetch()
        deps.log(f"{label} HTTP {code}")
        if code == 404:
            return code
        if deps.now() >= deadline:
            return code
        deps.sleep(deps.poll)


def _provider_env(base: dict[str, str] | None = None) -> tuple[dict[str, str], Log]:
    env = dict(os.environ if base is None else base)
    raw = env.get("REDISCLOUD_QA", "")
    secrets = [raw] if raw else []
    if raw.strip():
        mapped = map_secret(raw)
        env.update(mapped)
        secrets.extend(mapped.values())
    env.setdefault("PULUMI_CONFIG_PASSPHRASE", "")
    log = Log(secrets)
    log.absorb(
        {
            "api_key": env.get("REDISCLOUD_ACCESS_KEY", ""),
            "secret_key": env.get("REDISCLOUD_SECRET_KEY", ""),
        }
    )
    return env, log


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="QA nightly acceptance")
    parser.add_argument("--cleanup-only", action="store_true")
    args = parser.parse_args(argv)
    env, log = _provider_env()
    run_id = env.get("QA_RUN_ID") or env.get("GITHUB_RUN_ID") or "local"
    cloud = HttpCloud(
        env.get("REDISCLOUD_URL", ""),
        env.get("REDISCLOUD_ACCESS_KEY", ""),
        env.get("REDISCLOUD_SECRET_KEY", ""),
        log,
    )
    program = LiveProgram(env, log)
    provider = env.get("QA_CLOUD_PROVIDER", "AWS").strip().upper()
    region = env.get("QA_REGION", "us-east-1").strip()
    try:
        hold = int(env.get("QA_EVIDENCE_HOLD_SECONDS", "0"))
    except ValueError as exc:
        raise SuiteFailure("QA_EVIDENCE_HOLD_SECONDS is not an integer") from exc
    if provider not in {"AWS", "GCP"}:
        raise SuiteFailure("QA_CLOUD_PROVIDER must be AWS or GCP")
    if hold < 0 or hold > 1800:
        raise SuiteFailure("QA_EVIDENCE_HOLD_SECONDS must be between 0 and 1800")
    deps = Deps(
        env.get("REDISCLOUD_URL", ""),
        run_id,
        cloud,
        program,
        log,
        cloud_provider=provider,
        region=region,
        evidence_hold_seconds=hold,
    )
    try:
        if args.cleanup_only:
            cleanup_only(deps)
        else:
            run_acceptance(deps)
    except SuiteFailure as exc:
        log(str(exc))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
