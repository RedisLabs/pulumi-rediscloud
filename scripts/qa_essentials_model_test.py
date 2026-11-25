"""Exercise the proof model without Redis Cloud credentials or Pulumi CLI."""

import unittest

import qa_essentials_model as model
from qa_essentials_fake import FakeBackend


class EssentialsProofModelTest(unittest.TestCase):
    def test_exact_order_and_empty_inventory(self):
        api = FakeBackend()
        sub, db = model.run_model(api, "fake-account", "pulumi-proof-1")
        self.assertEqual((sub.identifier, db.identifier), ("10", "20"))
        self.assertEqual(api.events, [
            "lock", "inventory", "lock", "create subscription", "read subscription",
            "lock", "create database", "read subscription", "read database", "lock",
            "delete database", "read database", "read subscription", "lock",
            "delete subscription", "read subscription", "inventory",
        ])
        self.assertIsNone(api.sub)
        self.assertIsNone(api.db)

    def test_missing_lock_or_incomplete_inventory_never_creates(self):
        for which in ("lock", "inventory"):
            api = FakeBackend()
            if which == "lock": api.locked = False
            else: api.complete = False
            with self.subTest(which=which), self.assertRaises(model.ProofError):
                model.run_model(api, "fake-account", "pulumi-proof-1")
            self.assertNotIn("create subscription", api.events)

    def test_foreign_existing_resource_stops_before_creation(self):
        api = FakeBackend()
        api.sub = model.Resource("fake-account", "", "999", "pulumi-proof-1")
        with self.assertRaises(model.ProofError):
            model.run_model(api, "fake-account", "pulumi-proof-1")
        self.assertNotIn("create subscription", api.events)
        self.assertNotIn("delete subscription", api.events)

    def test_wrong_parent_binding_stops_without_delete(self):
        api = FakeBackend()
        original = api.create_database
        def wrong_parent(account, parent, name):
            db = original(account, parent, name)
            return model.Resource(db.account, "999", db.identifier, db.name)
        api.create_database = wrong_parent
        with self.assertRaises(model.ProofError):
            model.run_model(api, "fake-account", "pulumi-proof-1")
        self.assertNotIn("delete database", api.events)
        self.assertNotIn("delete subscription", api.events)

    def test_wrong_subscription_read_prevents_child_creation(self):
        api = FakeBackend()
        def wrong_identity(account, identifier):
            api.events.append("read subscription")
            return 200, model.Resource(account, "", "999", "pulumi-proof-1")
        api.read_subscription = wrong_identity
        with self.assertRaises(model.ProofError):
            model.run_model(api, "fake-account", "pulumi-proof-1")
        self.assertNotIn("create database", api.events)
        self.assertNotIn("delete subscription", api.events)

    def test_non_active_database_prevents_both_deletes(self):
        api = FakeBackend()
        read = api.read_database
        def provisioning(account, parent, identifier):
            code, db = read(account, parent, identifier)
            return code, model.Resource(db.account, db.parent, db.identifier, db.name, "provisioning")
        api.read_database = provisioning
        with self.assertRaises(model.ProofError):
            model.run_model(api, "fake-account", "pulumi-proof-1")
        self.assertNotIn("delete database", api.events)
        self.assertNotIn("delete subscription", api.events)

    def test_unauthenticated_absence_keeps_parent(self):
        api = FakeBackend()
        read = api.read_database
        def forbidden_after_delete(account, parent, identifier):
            if api.db is None:
                api.events.append("read database")
                return 403, None
            return read(account, parent, identifier)
        api.read_database = forbidden_after_delete
        with self.assertRaises(model.ProofError):
            model.run_model(api, "fake-account", "pulumi-proof-1")
        self.assertNotIn("delete subscription", api.events)
        self.assertIsNotNone(api.sub)

    def test_lock_loss_before_child_delete_prevents_both_deletes(self):
        api = FakeBackend()
        read = api.read_database
        def lose_lock(account, parent, identifier):
            value = read(account, parent, identifier)
            api.locked = False
            return value
        api.read_database = lose_lock
        with self.assertRaises(model.ProofError):
            model.run_model(api, "fake-account", "pulumi-proof-1")
        self.assertNotIn("delete database", api.events)
        self.assertNotIn("delete subscription", api.events)

    def test_lost_lock_after_child_absence_prevents_parent_delete(self):
        api = FakeBackend()
        read = api.read_database
        def lose_lock_after_delete(account, parent, identifier):
            result = read(account, parent, identifier)
            if result[0] == 404:
                api.locked = False
            return result
        api.read_database = lose_lock_after_delete
        with self.assertRaises(model.ProofError):
            model.run_model(api, "fake-account", "pulumi-proof-1")
        self.assertIn("delete database", api.events)
        self.assertNotIn("delete subscription", api.events)
        self.assertIsNotNone(api.sub)

    def test_lost_create_response_preserves_unknown_resources(self):
        for kind in ("subscription", "database"):
            api = FakeBackend()
            if kind == "subscription":
                create = api.create_subscription
                def lose_subscription(account, name):
                    create(account, name)
                    raise model.ProofError("response lost")
                api.create_subscription = lose_subscription
            else:
                create = api.create_database
                def lose_database(account, parent, name):
                    create(account, parent, name)
                    raise model.ProofError("response lost")
                api.create_database = lose_database
            with self.subTest(kind=kind), self.assertRaises(model.ProofError):
                model.run_model(api, "fake-account", "pulumi-proof-1")
            self.assertIsNotNone(api.sub)
            if kind == "database": self.assertIsNotNone(api.db)
            self.assertNotIn("delete database", api.events)
            self.assertNotIn("delete subscription", api.events)

    def test_lost_delete_response_never_starts_parent_delete(self):
        api = FakeBackend()
        delete = api.delete_database
        def lose_response(db):
            delete(db)
            raise model.ProofError("delete response lost")
        api.delete_database = lose_response
        with self.assertRaises(model.ProofError):
            model.run_model(api, "fake-account", "pulumi-proof-1")
        self.assertIsNotNone(api.sub)
        self.assertIsNone(api.db)
        self.assertNotIn("delete subscription", api.events)


if __name__ == "__main__":
    unittest.main()
