from contextlib import contextmanager
from django.db import connections


class QueriesDisabledError(Exception):
    pass


def _fake(*args, **kwargs):
    raise QueriesDisabledError()


def _apply_monkeypatch():
    for connection in connections.all():
        connection._zen_queries_depth = getattr(connection, "_zen_queries_depth", 0) + 1
        if connection._zen_queries_depth == 1:
            connection._real_create_cursor = connection.create_cursor
            connection.create_cursor = _fake


def _remove_monkeypatch():
    for connection in connections.all():
        if not hasattr(connection, "_zen_queries_depth"):
            assert hasattr(
                connection, "_real_create_cursor"
            ), "Cannot enable queries, not currently inside a queries_disabled block"
        connection._zen_queries_depth -= 1
        if connection._zen_queries_depth == 0:
            connection.create_cursor = connection._real_create_cursor
            del connection._real_create_cursor
            del connection._zen_queries_depth


@contextmanager
def queries_disabled():
    _apply_monkeypatch()
    try:
        yield
    finally:
        _remove_monkeypatch()


@contextmanager
def queries_dangerously_enabled():
    _remove_monkeypatch()
    try:
        yield
    finally:
        _apply_monkeypatch()
