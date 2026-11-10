#!/usr/bin/env python3
"""Hermetic tests for the QA nightly wrapper.

The HTTP server is local. These tests do not call Redis Cloud.
"""

from __future__ import annotations

import hashlib
import json
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import qa_live

REPO = Path(__file__).resolve().parents[1]
ACCESS_KEY = "access-sentinel-8c1e"
SECRET_KEY = "secret-sentinel-8c1e"
PAYMENT_ID = "pay-sentinel-8c1e"
PUBLIC_ENDPOINT = "pub-sentinel-8c1e.example"
PRIVATE_ENDPOINT = "priv-sentinel-8c1e.example"
SENTINELS = (ACCESS_KEY, SECRET_KEY, PAYMENT_ID, PUBLIC_ENDPOINT, PRIVATE_ENDPOINT)


class FakeProgram:
    def __init__(self, database_error: BaseException | None = None, names: list[str] | None = None) -> None:
        self.database_error = database_error
        self.names = names or [
            "databaseId",
            "privateEndpoint",
            "publicEndpoint",
            "subscriptionId",
        ]
        self.creates: list[tuple[str, str]] = []
        self.databases: list[tuple[str, str]] = []
        self.deletes: list[str] = []
        self.destroys = 0
        self.subscription_id = "101"
        self.database_id = "202"
        self.server = None

    def create_subscription(self, name: str, cidr: str) -> str:
        self.creates.append((name, cidr))
        return self.subscription_id

    def create_database(self, name: str, subscription_id: str) -> str:
        self.databases.append((name, subscription_id))
        if self.database_error is not None:
            raise self.database_error
        return self.database_id

    def output_names(self) -> list[str]:
        return list(self.names)

    def delete_subscription(self, subscription_id: str) -> None:
        self.deletes.append(subscription_id)

    def destroy(self) -> None:
        self.destroys += 1
        if self.server is not None:
            self.server.destroyed = True


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:
        self._handle("GET")

    def do_DELETE(self) -> None:
        self._handle("DELETE")

    def do_POST(self) -> None:
        self._handle("POST")

    def do_PUT(self) -> None:
        self._handle("PUT")

    def _handle(self, method: str) -> None:
        path = urllib.parse.urlsplit(self.path).path
        self.server.requests.append((method, path))
        if method == "POST" or method == "PUT":
            self._send(500, {"error": "create is not allowed from the wrapper"})
            return
        if method == "DELETE":
            parts = path.strip("/").split("/")
            if self.server.drop_deleted and parts[:2] == ["v1", "subscriptions"] and len(parts) == 3:
                sub_id = parts[2]
                self.server.subscriptions = [
                    row
                    for row in self.server.subscriptions
                    if str(row.get("id")) != sub_id
                ]
            self._send(200, {})
            return
        body = self.server.route_get(path)
        if body is None:
            self._send(404, {})
            return
        self._send(200, body)

    def _send(self, code: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class CloudServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, subscriptions: list, drop_deleted: bool = True) -> None:
        super().__init__(("127.0.0.1", 0), Handler)
        self.subscriptions = subscriptions
        self.drop_deleted = drop_deleted
        self.requests: list[tuple[str, str]] = []
        self.destroyed = False
        self.headers: list[tuple[str, str]] = []

    def route_get(self, path: str) -> dict | None:
        if self.destroyed and path != "/v1/subscriptions":
            return None
        if path == "/v1/subscriptions":
            return {"subscriptions": self.subscriptions}
        if path == "/v1/subscriptions/101":
            return {
                "id": 101,
                "name": "pulumi-ci-run",
                "status": "active",
                "paymentMethodId": PAYMENT_ID,
            }
        if path == "/v1/subscriptions/101/databases/202":
            return {
                "databaseId": 202,
                "status": "active",
                "publicEndpoint": PUBLIC_ENDPOINT,
                "privateEndpoint": PRIVATE_ENDPOINT,
            }
        if path == "/v1/subscriptions/101/databases":
            return {"subscription": [{"subscriptionId": 101, "databases": []}]}
        return None


class ServerHandle:
    def __init__(self, subscriptions: list, drop_deleted: bool = True) -> None:
        self.httpd = CloudServer(subscriptions, drop_deleted=drop_deleted)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)

    @property
    def requests(self) -> list[tuple[str, str]]:
        return self.httpd.requests


def forwarder(port: int, seen: list[str]):
    def opener(request, timeout=60):
        parsed = urllib.parse.urlsplit(request.full_url)
        seen.append(parsed.hostname or "")
        headers = {name.lower(): value for name, value in request.header_items()}
        key = headers.get("x-api-key", "")
        secret = headers.get("x-api-secret-key", "")
        opener.digests.append(
            (
                hashlib.sha256(key.encode()).hexdigest(),
                hashlib.sha256(secret.encode()).hexdigest(),
            )
        )
        local = urllib.parse.urlunsplit(("http", f"127.0.0.1:{port}", parsed.path, parsed.query, ""))
        forwarded = urllib.request.Request(local, data=request.data, method=request.get_method())
        try:
            return urllib.request.urlopen(forwarded, timeout=timeout)
        except urllib.error.HTTPError:
            raise

    opener.digests = []
    return opener


def deps_for(url: str, program: FakeProgram, opener, run_id: str = "run"):
    log = qa_live.Log([ACCESS_KEY, SECRET_KEY, PAYMENT_ID, PUBLIC_ENDPOINT, PRIVATE_ENDPOINT])
    cloud = qa_live.HttpCloud(url, ACCESS_KEY, SECRET_KEY, log, opener=opener)
    clock = {"t": 0.0}

    def now() -> float:
        return clock["t"]

    def sleep(seconds: float) -> None:
        clock["t"] += seconds

    return qa_live.Deps(url, run_id, cloud, program, log, sleep=sleep, now=now)


def assert_clean(test: unittest.TestCase, log: qa_live.Log) -> None:
    blob = "\n".join(log.lines)
    for secret in SENTINELS:
        if secret in blob:
            test.fail("log contains a forbidden value")
    if "[redacted]" in blob:
        test.fail("log redacted a value it should not have printed")


class QaLiveTest(unittest.TestCase):
    def test_target_configuration_normalizes_values_and_defaults_region_by_provider(self) -> None:
        self.assertEqual(qa_live.target_configuration({}), ("AWS", "us-east-1", 0))
        self.assertEqual(
            qa_live.target_configuration(
                {
                    "QA_CLOUD_PROVIDER": "  gcp ",
                    "QA_REGION": "  ",
                    "QA_EVIDENCE_HOLD_SECONDS": "12",
                }
            ),
            ("GCP", "us-central1", 12),
        )
        self.assertEqual(
            qa_live.target_configuration(
                {"QA_CLOUD_PROVIDER": " aws ", "QA_REGION": " eu-west-1 "}
            ),
            ("AWS", "eu-west-1", 0),
        )

    def test_live_program_config_uses_validated_target_values(self) -> None:
        calls: list[list[str]] = []
        program = qa_live.LiveProgram({}, qa_live.Log(), "GCP", "us-central1")
        program._name = "test-name"
        program._cidr = "10.0.0.0/24"
        program._pulumi = lambda args, check=True: calls.append(args) or 0

        program._config(include_database=False)

        self.assertIn(["config", "set", "cloudProvider", "GCP"], calls)
        self.assertIn(["config", "set", "region", "us-central1"], calls)

    def test_leftover_pulumi_ci_subscription_is_deleted_before_create(self) -> None:
        subscriptions = [
            {
                "id": 555,
                "name": "pulumi-ci-already",
                "status": "active",
                "paymentMethodId": PAYMENT_ID,
                "cloudDetails": [
                    {"regions": [{"networking": [{"deploymentCIDR": "10.0.0.0/24"}]}]}
                ],
            },
            {
                "id": 7,
                "name": "kept-subscription",
                "status": "active",
                "cloudDetails": [
                    {"regions": [{"networking": [{"deploymentCIDR": "10.1.0.0/24"}]}]}
                ],
            },
        ]
        server = ServerHandle(subscriptions)
        try:
            program = FakeProgram()
            program.server = server.httpd
            hosts: list[str] = []
            opener = forwarder(server.httpd.server_address[1], hosts)
            deps = deps_for("https://qa.example.test/v1/", program, opener, run_id="run42")
            qa_live.run_acceptance(deps)
            names = [str(row.get("name")) for row in server.httpd.subscriptions]
            self.assertNotIn("pulumi-ci-already", names)
            self.assertIn("kept-subscription", names)
            self.assertEqual(program.creates, [("pulumi-ci-run42", "10.0.0.0/24")])
            methods = [method for method, _path in server.requests]
            self.assertIn("DELETE", methods)
            self.assertNotIn("POST", methods)
            self.assertNotIn("PUT", methods)
            assert_clean(self, deps.log)
        finally:
            server.close()

    def test_leftover_that_stays_refuses_create(self) -> None:
        subscriptions = [
            {
                "id": 555,
                "name": "pulumi-ci-already",
                "status": "active",
            }
        ]
        server = ServerHandle(subscriptions, drop_deleted=False)
        try:
            program = FakeProgram()
            hosts: list[str] = []
            opener = forwarder(server.httpd.server_address[1], hosts)
            deps = deps_for("https://qa.example.test/v1/", program, opener)
            with self.assertRaises(qa_live.SuiteFailure):
                qa_live.run_acceptance(deps)
            self.assertEqual(program.creates, [])
            self.assertIn("DELETE", [method for method, _path in server.requests])
            assert_clean(self, deps.log)
        finally:
            server.close()

    def test_cleanup_only_leaves_another_pulumi_ci_name(self) -> None:
        subscriptions = [
            {
                "id": 555,
                "name": "pulumi-ci-already",
                "status": "active",
                "paymentMethodId": PAYMENT_ID,
            }
        ]
        server = ServerHandle(subscriptions)
        try:
            program = FakeProgram()
            hosts: list[str] = []
            opener = forwarder(server.httpd.server_address[1], hosts)
            deps = deps_for("https://qa.example.test/v1/", program, opener)
            qa_live.cleanup_only(qa_live.Deps(
                deps.url,
                "other-run",
                deps.cloud,
                program,
                deps.log,
                sleep=deps.sleep,
                now=deps.now,
            ))
            self.assertNotIn("DELETE", [method for method, _path in server.requests])
            self.assertEqual(server.httpd.subscriptions[0]["name"], "pulumi-ci-already")
            assert_clean(self, deps.log)
        finally:
            server.close()

    def test_failed_database_step_deletes_the_subscription(self) -> None:
        server = ServerHandle(
            [
                {
                    "id": 7,
                    "name": "kept-subscription",
                    "status": "active",
                    "cloudDetails": [
                        {"regions": [{"networking": [{"deploymentCIDR": "10.0.0.0/24"}]}]}
                    ],
                }
            ]
        )
        try:
            program = FakeProgram(database_error=RuntimeError("database step failed"))
            hosts: list[str] = []
            opener = forwarder(server.httpd.server_address[1], hosts)
            deps = deps_for("https://qa.example.test/v1", program, opener, run_id="run42")
            with self.assertRaises(RuntimeError):
                qa_live.run_acceptance(deps)
            self.assertEqual(program.creates, [("pulumi-ci-run42", "10.0.1.0/24")])
            self.assertEqual(program.databases, [("pulumi-ci-run42", "101")])
            self.assertEqual(program.deletes, ["101"])
            self.assertEqual(program.destroys, 0)
            self.assertNotIn("POST", [method for method, _path in server.requests])
            self.assertNotIn(("DELETE", "/v1/subscriptions/7"), server.requests)
            self.assertTrue(any("database step failed" in line for line in deps.log.lines))
            assert_clean(self, deps.log)
        finally:
            server.close()

    def test_success_requires_active_endpoint_names_and_http_404(self) -> None:
        server = ServerHandle(
            [
                {
                    "id": 7,
                    "name": "kept-subscription",
                    "status": "active",
                    "paymentMethodId": PAYMENT_ID,
                    "cloudDetails": [
                        {
                            "regions": [
                                {
                                    "networking": [
                                        {"deploymentCIDR": "10.0.0.0/24"},
                                        {"deploymentCidr": "10.0.1.0/24"},
                                    ]
                                }
                            ]
                        }
                    ],
                }
            ]
        )
        try:
            program = FakeProgram()
            program.server = server.httpd
            hosts: list[str] = []
            opener = forwarder(server.httpd.server_address[1], hosts)
            deps = deps_for("https://qa.example.test/v1/", program, opener, run_id="run7")
            qa_live.run_acceptance(deps)
            self.assertEqual(program.creates, [("pulumi-ci-run7", "10.0.2.0/24")])
            self.assertEqual(program.databases, [("pulumi-ci-run7", "101")])
            self.assertEqual(program.destroys, 1)
            self.assertEqual(program.deletes, [])
            self.assertIn(("GET", "/v1/subscriptions/101"), server.requests)
            self.assertIn(("GET", "/v1/subscriptions/101/databases/202"), server.requests)
            blob = "\n".join(deps.log.lines)
            self.assertIn("publicEndpoint", blob)
            self.assertIn("privateEndpoint", blob)
            self.assertIn("subscription HTTP 200 status active", blob)
            self.assertIn("database HTTP 200 status active", blob)
            self.assertIn("subscription HTTP 404", blob)
            self.assertIn("database HTTP 404", blob)
            self.assertIn("qa live ok", blob)
            self.assertNotIn(PUBLIC_ENDPOINT, blob)
            self.assertNotIn(PRIVATE_ENDPOINT, blob)
            assert_clean(self, deps.log)
            self.assertEqual(
                opener.digests[0],
                (
                    hashlib.sha256(ACCESS_KEY.encode()).hexdigest(),
                    hashlib.sha256(SECRET_KEY.encode()).hexdigest(),
                ),
            )
            self.assertTrue(all(host == "qa.example.test" for host in hosts))
        finally:
            server.close()

    def test_bad_urls_refuse_before_create(self) -> None:
        refused = [
            "",
            "   ",
            None,
            "http://qa.example.test/v1",
            "http://api.redislabs.com/v1",
            "ftp://qa.example.test/v1",
            "https://api.redislabs.com",
            "https://api.redislabs.com/",
            "https://api.redislabs.com/v1",
            "https://api.redislabs.com/v1/",
            "https://api.redislabs.com/v1/subscriptions",
            "https://API.RedisLabs.com/anything/",
            "https://api.redislabs.com:443/v1",
            "https://user:secret@api.redislabs.com/v1/",
            "https://qa.api.redislabs.com",
            "https://qa.api.redislabs.com/",
            "https://qa.api.redislabs.com/v1/extra",
            "https://a.b.api.redislabs.com/v1",
        ]
        for url in refused:
            calls: list[str] = []

            def opener(request, timeout=60, calls=calls):
                calls.append(request.full_url)
                raise AssertionError("HTTP was attempted")

            program = FakeProgram()
            log = qa_live.Log()
            cloud = qa_live.HttpCloud(url, ACCESS_KEY, SECRET_KEY, log, opener=opener)
            deps = qa_live.Deps(url, "run", cloud, program, log, sleep=lambda _s: None, now=lambda: 0.0)
            with self.assertRaises(qa_live.SuiteFailure):
                qa_live.run_acceptance(deps)
            self.assertEqual(program.creates, [])
            self.assertEqual(program.deletes, [])
            self.assertEqual(calls, [])

        source = (REPO / "scripts" / "qa_live.py").read_text()
        self.assertNotIn("https://api.redislabs.com", source)
        self.assertNotIn("https://" + "api.redislabs.com", source)

    def test_cidr_picker_skips_only_deployment_cidrs_on_the_account(self) -> None:
        self.assertEqual(qa_live.choose_cidr(set()), "10.0.0.0/24")
        used = {"10.0.0.0/24", "10.0.1.0/24"}
        chosen = qa_live.choose_cidr(used)
        self.assertNotIn(chosen, used)
        self.assertEqual(chosen, "10.0.2.0/24")
        source = (REPO / "scripts" / "qa_live.py").read_text()
        self.assertNotIn("HELD_CIDRS", source)
        self.assertNotIn("reserved", source.lower())

    def test_program_creates_resources_from_subscription_output(self) -> None:
        program = (REPO / "examples" / "qa" / "main.go").read_text()
        self.assertIn("GetPaymentMethod", program)
        self.assertIn("PaymentMethodId: pulumi.String(card.Id)", program)
        self.assertNotIn('PaymentMethodId: pulumi.String("', program)
        self.assertIn("NewAclRule", program)
        self.assertIn("NewSubscription", program)
        self.assertIn("NewSubscriptionDatabase", program)
        self.assertIn("SubscriptionId:", program)
        self.assertIn("subscription.ID()", program)
        self.assertIn('pulumi.String("operations-per-second")', program)
        self.assertIn("DatasetSizeInGb:", program)
        self.assertIn("NetworkingDeploymentCidr:", program)
        self.assertIn("pulumi.String(cidr)", program)
        self.assertIn('ctx.Export("publicEndpoint"', program)
        self.assertIn('ctx.Export("privateEndpoint"', program)
        gomod = (REPO / "examples" / "qa" / "go.mod").read_text()
        self.assertIn("github.com/RedisLabs/pulumi-rediscloud/sdk", gomod)
        self.assertIn("replace github.com/RedisLabs/pulumi-rediscloud/sdk => ../../sdk", gomod)

    def test_workflow_is_schedule_and_dispatch_only(self) -> None:
        text = (REPO / ".github" / "workflows" / "qa-live.yaml").read_text()
        self.assertNotIn("pull_request", text)
        self.assertNotIn("ci-success", text)
        self.assertIn('cron: "17 8 * * *"', text)
        self.assertIn("workflow_dispatch", text)
        self.assertIn("description: Provider region (defaults by cloud provider)", text)
        self.assertIn("QA_REGION: ${{ inputs.region || '' }}", text)
        self.assertIn("group: qa-live", text)
        self.assertIn("cancel-in-progress: false", text)
        self.assertIn("timeout-minutes: 120", text)
        self.assertIn("pulumi login --local", text)
        self.assertIn("pulumi plugin install resource rediscloud 0.0.0 --file", text)
        self.assertIn("bin/pulumi-resource-rediscloud", text)
        self.assertIn('PULUMI_CONFIG_PASSPHRASE: ""', text)
        self.assertIn("secrets.REDISCLOUD_QA", text)
        self.assertIn("REDISCLOUD_ACCESS_KEY", text)
        self.assertIn("REDISCLOUD_SECRET_KEY", text)
        self.assertIn("REDISCLOUD_URL", text)
        self.assertIn("if: always()", text)
        self.assertNotIn("pulumi login --cloud", text)
        self.assertNotIn("api.github.com/RedisLabs/pulumi-rediscloud/releases", text)

    def test_map_secret_does_not_print_values(self) -> None:
        raw = json.dumps({"api_key": ACCESS_KEY, "secret_key": SECRET_KEY, "url": "https://qa.example.test/v1"})
        mapped = qa_live.map_secret(raw)
        self.assertEqual(mapped["REDISCLOUD_ACCESS_KEY"], ACCESS_KEY)
        self.assertEqual(mapped["REDISCLOUD_SECRET_KEY"], SECRET_KEY)
        self.assertEqual(mapped["REDISCLOUD_URL"], "https://qa.example.test/v1")
        missing_url = qa_live.map_secret(json.dumps({"api_key": ACCESS_KEY, "secret_key": SECRET_KEY}))
        self.assertEqual(missing_url["REDISCLOUD_URL"], "")
        with self.assertRaises(qa_live.SuiteFailure):
            qa_live.map_secret(json.dumps({"api_key": ACCESS_KEY}))
        log = qa_live.Log()
        try:
            qa_live.map_secret("{")
        except qa_live.SuiteFailure as exc:
            log(str(exc))
        self.assertNotIn(ACCESS_KEY, "\n".join(log.lines))


if __name__ == "__main__":
    unittest.main()
