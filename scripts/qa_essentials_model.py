"""Credential-free model of the desired Essentials lifecycle proof.

This module provides no real Cloud, Pulumi or lock adapter and is not an
executable live test. Its protocol is an assertion target for a future driver;
implementing an adapter does not by itself establish the required shared lock,
ownership journal or safe crash recovery.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ProofError(Exception):
    """The proof stopped; resources may still exist and require recovery."""


@dataclass(frozen=True)
class Resource:
    account: str
    parent: str
    identifier: str
    name: str
    status: str = "active"


class Backend(Protocol):
    def assert_lock(self) -> None: ...
    def inventory(self, account: str, name: str) -> tuple[bool, list[Resource]]: ...
    def create_subscription(self, account: str, name: str) -> Resource: ...
    def create_database(self, account: str, parent: str, name: str) -> Resource: ...
    def read_subscription(self, account: str, identifier: str) -> tuple[int, Resource | None]: ...
    def read_database(self, account: str, parent: str, identifier: str) -> tuple[int, Resource | None]: ...
    def delete_database(self, resource: Resource) -> None: ...
    def delete_subscription(self, resource: Resource) -> None: ...


def _identity(resource: Resource, account: str, parent: str, name: str) -> bool:
    return (resource.account == account and resource.parent == parent and
            resource.name == name and resource.identifier.isascii() and
            resource.identifier.isdigit() and int(resource.identifier) > 0)


def _read(expected: Resource, result: tuple[int, Resource | None]) -> None:
    code, resource = result
    if (code != 200 or resource is None or resource.status != "active" or
            (resource.account, resource.parent, resource.identifier, resource.name) !=
            (expected.account, expected.parent, expected.identifier, expected.name)):
        raise ProofError("authenticated exact active identity read did not match")


def run_model(backend: Backend, account: str, name: str) -> tuple[Resource, Resource]:
    """Exercise the proof order in a fake backend; stop on uncertain evidence.

    Failures deliberately do not trigger cleanup: unknown ownership or a lost
    outcome must not be resolved with direct deletes. This model has no durable
    journal and must never be used to authorize real Cloud operations.
    """
    if not account or not name.startswith("pulumi-proof-"):
        raise ProofError("invalid run identity")
    backend.assert_lock()
    complete, rows = backend.inventory(account, name)
    if not complete or rows:
        raise ProofError("preflight inventory incomplete or not empty")

    backend.assert_lock()
    sub = backend.create_subscription(account, name)
    if not _identity(sub, account, "", name):
        raise ProofError("untrusted subscription identity")
    _read(sub, backend.read_subscription(account, sub.identifier))

    backend.assert_lock()
    db = backend.create_database(account, sub.identifier, name)
    if not _identity(db, account, sub.identifier, name):
        raise ProofError("untrusted database identity")
    _read(sub, backend.read_subscription(account, sub.identifier))
    _read(db, backend.read_database(account, sub.identifier, db.identifier))

    backend.assert_lock()
    backend.delete_database(db)
    code, body = backend.read_database(account, sub.identifier, db.identifier)
    if code != 404 or body is not None:
        raise ProofError("database absence unverified")
    _read(sub, backend.read_subscription(account, sub.identifier))

    backend.assert_lock()
    backend.delete_subscription(sub)
    code, body = backend.read_subscription(account, sub.identifier)
    if code != 404 or body is not None:
        raise ProofError("subscription absence unverified")
    complete, rows = backend.inventory(account, name)
    if not complete or rows:
        raise ProofError("final inventory incomplete or not empty")
    return sub, db
