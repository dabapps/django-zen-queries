from contextlib import contextmanager
from django.db import connections


class QueriesDisabledError(Exception):
    pass


class QueriesDisabledCursor:
    query = None

    def execute(self, sql, *args, **kwargs):
        raise QueriesDisabledError(sql)

    def executemany(self, sql, *args, **kwargs):
        raise QueriesDisabledError(sql)

    def close(self):
        pass


def _create_queries_disabled_cursor(*args, **kwargs):
    return QueriesDisabledCursor()


def _apply_monkeypatch(connection):
    connection._queries_disabled = True
    connection._real_create_cursor = connection.create_cursor
    connection.create_cursor = _create_queries_disabled_cursor


def _remove_monkeypatch(connection):
    connection.create_cursor = connection._real_create_cursor
    del connection._real_create_cursor
    del connection._queries_disabled


def _disable_queries():
    for connection in connections.all():
        _apply_monkeypatch(connection)


def _enable_queries():
    for connection in connections.all():
        _remove_monkeypatch(connection)


def _are_queries_disabled():
    for connection in connections.all():
        return hasattr(connection, "_queries_disabled")


def _are_queries_dangerously_enabled():
    for connection in connections.all():
        return hasattr(connection, "_queries_dangerously_enabled")


def _mark_as_dangerously_enabled():
    for connection in connections.all():
        connection._queries_dangerously_enabled = True


def _mark_as_not_dangerously_enabled():
    for connection in connections.all():
        del connection._queries_dangerously_enabled


@contextmanager
def queries_disabled():
    queries_already_disabled = _are_queries_disabled()
    if not queries_already_disabled and not _are_queries_dangerously_enabled():
        _disable_queries()
    try:
        yield
    finally:
        if not queries_already_disabled and not _are_queries_dangerously_enabled():
            _enable_queries()


@contextmanager
def queries_dangerously_enabled():
    queries_dangerously_enabled_before = _are_queries_dangerously_enabled()
    if not queries_dangerously_enabled_before:
        _mark_as_dangerously_enabled()
    queries_disabled_before = _are_queries_disabled()
    if queries_disabled_before:
        _enable_queries()
    try:
        yield
    finally:
        if queries_disabled_before:
            _disable_queries()
        if not queries_dangerously_enabled_before:
            _mark_as_not_dangerously_enabled()
