from contextlib import contextmanager
from django.db import connections
from typing import Any, Callable, Dict, Generator


class QueriesDisabledError(Exception):
    pass


def _raise_exception(
    execute: Callable[[str, Any, bool, Dict[str, Any]], Any],
    sql: str,
    params: Any,
    many: bool,
    context: Dict[str, Any],
) -> Any:
    raise QueriesDisabledError(sql)


def _disable_queries() -> None:
    for connection in connections.all():
        connection.execute_wrappers.append(_raise_exception)


def _enable_queries() -> None:
    for connection in connections.all():
        connection.execute_wrappers.pop()


def _are_queries_disabled() -> bool:
    for connection in connections.all():
        return _raise_exception in connection.execute_wrappers
    return False


def _are_queries_dangerously_enabled() -> bool:
    for connection in connections.all():
        return hasattr(connection, "_queries_dangerously_enabled")
    return False


def _mark_as_dangerously_enabled() -> None:
    for connection in connections.all():
        connection._queries_dangerously_enabled = True


def _mark_as_not_dangerously_enabled() -> None:
    for connection in connections.all():
        del connection._queries_dangerously_enabled


@contextmanager
def queries_disabled() -> Generator[None, None, None]:
    queries_already_disabled = _are_queries_disabled()
    if not queries_already_disabled and not _are_queries_dangerously_enabled():
        _disable_queries()
    try:
        yield
    finally:
        if not queries_already_disabled and not _are_queries_dangerously_enabled():
            _enable_queries()


@contextmanager
def queries_dangerously_enabled() -> Generator[None, None, None]:
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
