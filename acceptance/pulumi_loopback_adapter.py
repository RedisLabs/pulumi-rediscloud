"""Run the real Pulumi provider against a strictly local fake HTTP service.

This is simulated evidence only. The fake account, task completion and lock do
not qualify Cloud behavior, cross-repository admission, ownership, or recovery.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.error
import urllib.parse
import urllib.request

from contract import Evidence, StepReceipt
from pulumi_simulated_adapter import LIFECYCLE

ROOT = Path(__file__).resolve().parents[1]


class FixtureServer(ThreadingHTTPServer):
    def __init__(self):
        super().__init__(("127.0.0.1", 0), FixtureHandler)
        self.sub = False
        self.db = False
        self.eviction = "volatile-lru"
        self.events = []
        self.violations = []
        self.lock = threading.Lock()


class FixtureHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, code, body):
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(raw)

    def dispatch(self):
        path = self.path.split("?", 1)[0]
        with self.server.lock:
            self.server.events.append((self.command, path))
            if self.headers.get("X-Api-Key") != "fake" or self.headers.get("X-Api-Secret-Key") != "fake":
                self.server.violations.append("authentication")
                return self.reply(403, {"error": "dummy auth required"})
            if self.command in ("POST", "PUT", "DELETE"):
                task = ""
                body = {}
                if self.command in ("POST", "PUT"):
                    length = int(self.headers.get("Content-Length", "0"))
                    if length > 1024 * 1024:
                        self.server.violations.append("oversized body")
                        return self.reply(400, {"error": "fixture body too large"})
                    try:
                        body = json.loads(self.rfile.read(length))
                    except (ValueError, UnicodeDecodeError):
                        self.server.violations.append("malformed body")
                        return self.reply(400, {"error": "invalid fixture body"})
                if self.command == "POST" and path == "/v1/fixed/subscriptions" and not self.server.sub:
                    if any(body.get(key) != value for key, value in {"name": "fixture", "planId": 7, "paymentMethod": "credit-card", "paymentMethodId": 3}.items()):
                        self.server.violations.append("wrong subscription payload")
                        return self.reply(400, {"error": "wrong fixture subscription payload"})
                    self.server.sub, task = True, "subcreate"
                elif self.command == "POST" and path == "/v1/fixed/subscriptions/1/databases" and self.server.sub and not self.server.db:
                    if any(body.get(key) != value for key, value in {"name": "fixture", "dataPersistence": "none", "dataEvictionPolicy": "volatile-lru", "replication": False}.items()):
                        self.server.violations.append("wrong database payload")
                        return self.reply(400, {"error": "wrong fixture database payload"})
                    self.server.db, task = True, "dbcreate"
                elif self.command == "PUT" and path == "/v1/fixed/subscriptions/1/databases/2" and self.server.db:
                    if body.get("dataEvictionPolicy") not in {"volatile-lru", "allkeys-lru"}:
                        self.server.violations.append("unexpected eviction policy")
                        return self.reply(400, {"error": "unexpected fixture eviction"})
                    self.server.eviction = body["dataEvictionPolicy"]
                    task = "dbupdate"
                elif self.command == "PUT" and path == "/v1/fixed/subscriptions/1/databases/2/tags" and self.server.db:
                    return self.reply(200, {"tags": []})
                elif self.command == "DELETE" and path == "/v1/fixed/subscriptions/1/databases/2" and self.server.db:
                    self.server.db, task = False, "dbdelete"
                elif self.command == "DELETE" and path == "/v1/fixed/subscriptions/1" and self.server.sub and not self.server.db:
                    self.server.sub, task = False, "subdelete"
                else:
                    self.server.violations.append("unexpected write")
                    return self.reply(400, {"error": "unexpected fixture write"})
                return self.reply(200, {"taskId": task})
            if path.startswith("/v1/tasks/"):
                task = path.rsplit("/", 1)[-1]
                if task not in {"subcreate", "dbcreate", "dbupdate", "dbdelete", "subdelete"}:
                    self.server.violations.append("unknown task")
                    return self.reply(404, {"error": "unknown fixture task"})
                identifier = 1 if task == "subcreate" else 2
                return self.reply(200, {"taskId": task, "status": "processing-completed", "response": {"resourceId": identifier}})
            if path == "/v1/fixed/subscriptions/1":
                if not self.server.sub:
                    return self.reply(404, {"message": "fixture not found"})
                return self.reply(200, {"id": 1, "name": "fixture", "status": "active", "planId": 7, "paymentMethod": "credit-card", "paymentMethodId": 3})
            if path == "/v1/fixed/subscriptions/1/databases/2/tags" and self.server.db:
                return self.reply(200, {"tags": []})
            if path == "/v1/fixed/subscriptions/1/databases/2":
                if not self.server.db:
                    return self.reply(404, {"message": "fixture not found"})
                return self.reply(200, {"databaseId": 2, "name": "fixture", "status": "active", "protocol": "redis", "provider": "GCP", "region": "us-central1", "dataPersistence": "none", "dataEvictionPolicy": self.server.eviction, "replication": False, "activatedOn": "2025-01-01T00:00:00Z", "security": {"defaultUserEnabled": True, "sourceIps": ["0.0.0.0/0"]}, "modules": [], "alerts": []})
            if path == "/v1/fixed/subscriptions":
                return self.reply(200, {"subscriptions": ([{"id": 1, "name": "fixture", "status": "active"}] if self.server.sub else [])})
            self.server.violations.append("unexpected read")
            return self.reply(404, {"error": "unsupported fixture path"})

    do_GET = do_POST = do_PUT = do_DELETE = dispatch


def _run(cli, program, env, *args):
    result = subprocess.run([cli, *args], cwd=program, env=env, capture_output=True, text=True, timeout=300, check=False)
    if result.returncode:
        detail = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())[-4000:]
        raise RuntimeError(f"pulumi {args[0]} failed with exit {result.returncode}: {detail}")
    return result.stdout


def _read(base, path, expected):
    req = urllib.request.Request(base + path, headers={"X-Api-Key": "fake", "X-Api-Secret-Key": "fake"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=5) as response:
            code, body = response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            code, body = exc.code, json.load(exc)
        finally:
            exc.close()
    if code != expected:
        raise AssertionError(f"fake authenticated read expected {expected}, got {code}")
    return body


def _fixture_env(pulumi_home, url):
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port or
            parsed.path != "/v1" or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("fixture URL must be an exact loopback HTTP endpoint")
    # Preserve only runtime paths, never any inherited Cloud credentials.
    env = {k: os.environ[k] for k in ("HOME", "LANG", "PATH", "USER", "TMPDIR", "GOPATH", "GOMODCACHE", "GOCACHE", "GOTOOLCHAIN", "GOROOT") if k in os.environ}
    env.update({"PULUMI_HOME": str(pulumi_home), "PULUMI_CONFIG_PASSPHRASE": "", "PULUMI_SKIP_UPDATE_CHECK": "true", "PULUMI_DISABLE_AUTOMATIC_PLUGIN_ACQUISITION": "true", "REDISCLOUD_ACCESS_KEY": "fake", "REDISCLOUD_SECRET_KEY": "fake", "REDISCLOUD_URL": url, "HTTP_PROXY": "http://127.0.0.1:1", "HTTPS_PROXY": "http://127.0.0.1:1", "NO_PROXY": "127.0.0.1,localhost"})
    return env


def run_loopback(cli, provider, update_eviction=False):
    """Run the CLI and repository-built provider using disposable local state."""
    cli = shutil.which(cli) or cli
    cli, provider = str(Path(cli).resolve(strict=True)), str(Path(provider).resolve(strict=True))
    server = FixtureServer()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory(prefix="pulumi-loopback-") as directory:
            base = Path(directory)
            program, backend, pulumi_home = base / "program", base / "backend", base / "pulumi-home"
            for folder in (program, backend, pulumi_home):
                folder.mkdir()
            mod = (ROOT / "examples/qa/go.mod").read_text()
            needle = "replace github.com/RedisLabs/pulumi-rediscloud/sdk => ../../sdk"
            if mod.count(needle) != 1:
                raise RuntimeError("SDK replace target is unexpected")
            (program / "go.mod").write_text(mod.replace(needle, f"replace github.com/RedisLabs/pulumi-rediscloud/sdk => {ROOT / 'sdk'}"))
            shutil.copyfile(ROOT / "examples/qa/go.sum", program / "go.sum")
            shutil.copyfile(ROOT / "acceptance/loopback_program.go", program / "main.go")
            (program / "Pulumi.yaml").write_text("name: local-fixture\nruntime: go\ndescription: isolated loopback test\n")
            url = f"http://127.0.0.1:{server.server_port}/v1"
            env = _fixture_env(pulumi_home, url)
            _run(cli, program, env, "login", f"file://{backend}")
            _run(cli, program, env, "plugin", "install", "resource", "rediscloud", "0.0.0", "--file", provider)
            _run(cli, program, env, "stack", "init", "fixture")
            _run(cli, program, env, "config", "set", "rediscloud:url", url)
            _run(cli, program, env, "config", "set", "includeDatabase", "false")
            if _read(url, "/fixed/subscriptions", 200)["subscriptions"] != []:
                raise AssertionError("fixture baseline not empty")
            print("SIMULATED LOOPBACK: empty fixed-subscription baseline", flush=True)
            _run(cli, program, env, "up", "--yes", "--skip-preview", "--non-interactive")
            parent = _read(url, "/fixed/subscriptions/1", 200)
            if parent.get("status") != "active" or parent.get("id") != 1 or parent.get("name") != "fixture":
                raise AssertionError("fixture subscription identity or status differs")
            print("SIMULATED LOOPBACK: parent ID 1 authenticated 200 active", flush=True)
            _run(cli, program, env, "config", "set", "includeDatabase", "true")
            _run(cli, program, env, "up", "--yes", "--skip-preview", "--non-interactive")
            outputs = json.loads(_run(cli, program, env, "stack", "output", "--json"))
            if str(outputs.get("sub")) != "1" or outputs.get("db") != 2:
                raise AssertionError("provider returned unexpected fixture identities")
            child = _read(url, "/fixed/subscriptions/1/databases/2", 200)
            if child.get("status") != "active" or child.get("databaseId") != 2 or child.get("name") != "fixture":
                raise AssertionError("fixture database identity or status differs")
            parent = _read(url, "/fixed/subscriptions/1", 200)
            if parent.get("status") != "active" or parent.get("id") != 1:
                raise AssertionError("fixture parent identity or status differs")
            print("SIMULATED LOOPBACK: child ID 2 and parent ID 1 authenticated 200 active", flush=True)
            if update_eviction:
                _run(cli, program, env, "config", "set", "eviction", "allkeys-lru")
                _run(cli, program, env, "up", "--yes", "--skip-preview", "--non-interactive")
                outputs = json.loads(_run(cli, program, env, "stack", "output", "--json"))
                changed = _read(url, "/fixed/subscriptions/1/databases/2", 200)
                parent = _read(url, "/fixed/subscriptions/1", 200)
                if (str(outputs.get("sub")) != "1" or outputs.get("db") != 2 or
                        changed.get("databaseId") != 2 or changed.get("status") != "active" or
                        changed.get("dataEvictionPolicy") != "allkeys-lru" or parent.get("id") != 1):
                    raise AssertionError("fixture update readback or identities differ")
                print("SIMULATED LOOPBACK: eviction updated to allkeys-lru with IDs 1 and 2 unchanged", flush=True)
            _run(cli, program, env, "config", "set", "includeDatabase", "false")
            _run(cli, program, env, "up", "--yes", "--skip-preview", "--non-interactive")
            _read(url, "/fixed/subscriptions/1/databases/2", 404)
            if _read(url, "/fixed/subscriptions/1", 200).get("id") != 1:
                raise AssertionError("fixture parent identity changed")
            print("SIMULATED LOOPBACK: child ID 2 authenticated 404 while parent ID 1 is 200", flush=True)
            _run(cli, program, env, "destroy", "--yes", "--skip-preview", "--non-interactive")
            _read(url, "/fixed/subscriptions/1", 404)
            if _read(url, "/fixed/subscriptions", 200)["subscriptions"] != []:
                raise AssertionError("fixture final inventory not empty")
            print("SIMULATED LOOPBACK: parent ID 1 authenticated 404 and fake inventory empty", flush=True)
            with server.lock:
                if server.violations or server.sub or server.db:
                    raise AssertionError("unexpected fixture traffic or residual state")
                writes = [(method, path) for method, path in server.events if method in {"POST", "PUT", "DELETE"}]
            expected = [("POST", "/v1/fixed/subscriptions"), ("POST", "/v1/fixed/subscriptions/1/databases"), ("PUT", "/v1/fixed/subscriptions/1/databases/2"), ("PUT", "/v1/fixed/subscriptions/1/databases/2/tags")]
            if update_eviction:
                expected.extend([("PUT", "/v1/fixed/subscriptions/1/databases/2"), ("PUT", "/v1/fixed/subscriptions/1/databases/2/tags")])
            expected.extend([("DELETE", "/v1/fixed/subscriptions/1/databases/2"), ("DELETE", "/v1/fixed/subscriptions/1")])
            if writes != expected:
                raise AssertionError(f"unexpected fixture mutation sequence: {writes}")
            print("SIMULATED LOOPBACK: provider mutation order matched", flush=True)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)


class PulumiLoopbackAdapter:
    """Shared contract consumer with an isolated fake service, never a live run."""

    def __init__(self, cli, provider):
        self.cli, self.provider = cli, provider

    def execute(self, scenario):
        base = dict(provider="pulumi", scenario_id=scenario.id, mode="simulated", source_revision="0" * 40, artifact_digest="", run_url="https://fixture.invalid/run", evidence_url="https://fixture.invalid/log", direct_cloud_recovery=False)
        update = scenario.id == "essentials-database-eviction-update"
        if scenario.id not in {"essentials-database-lifecycle", "essentials-database-eviction-update"}:
            return Evidence(**base, steps=(), outcome="unsupported", cleanup="not_started")
        expected_steps = LIFECYCLE[:5] + ("update_eviction", "read_updated_eviction_same_identity") + LIFECYCLE[5:] if update else LIFECYCLE
        if scenario.steps != expected_steps:
            return Evidence(**base, steps=(), outcome="blocked", cleanup="not_started")
        try:
            run_loopback(self.cli, self.provider, update_eviction=update)
        except (AssertionError, OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as exc:
            print(f"SIMULATED LOOPBACK failed: {exc}", flush=True)
            return Evidence(**base, steps=(), outcome="fail", cleanup="unknown")
        # A disposable fake server establishes no cross-repository account
        # admission. Keep that step and the overall claim blocked even when
        # the provider's remaining loopback operations succeed.
        receipts = tuple(StepReceipt(step, "blocked" if i == 0 else "passed", f"https://fixture.invalid/loopback-only/{step}") for i, step in enumerate(expected_steps))
        return Evidence(**base, steps=receipts, outcome="blocked", cleanup="clean")
