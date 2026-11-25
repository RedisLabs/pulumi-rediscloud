"""In-memory backend used only by credential-free proof demonstrations."""

import qa_essentials_model as model


class FakeBackend:
    def __init__(self):
        self.events = []
        self.sub = None
        self.db = None
        self.locked = True
        self.complete = True

    def assert_lock(self):
        self.events.append("lock")
        if not self.locked:
            raise model.ProofError("lock lost")

    def inventory(self, account, name):
        self.events.append("inventory")
        return self.complete, [r for r in (self.sub, self.db) if r and r.account == account and r.name == name]

    def create_subscription(self, account, name):
        self.events.append("create subscription")
        self.sub = model.Resource(account, "", "10", name)
        return self.sub

    def create_database(self, account, parent, name):
        self.events.append("create database")
        self.db = model.Resource(account, parent, "20", name)
        return self.db

    def read_subscription(self, account, identifier):
        self.events.append("read subscription")
        return (200, self.sub) if self.sub else (404, None)

    def read_database(self, account, parent, identifier):
        self.events.append("read database")
        return (200, self.db) if self.db else (404, None)

    def delete_database(self, resource):
        self.events.append("delete database")
        if resource != self.db:
            raise AssertionError("not the created database")
        self.db = None

    def delete_subscription(self, resource):
        self.events.append("delete subscription")
        if resource != self.sub or self.db is not None:
            raise AssertionError("parent delete before exact child absence")
        self.sub = None
