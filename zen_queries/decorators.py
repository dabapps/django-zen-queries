from contextlib import contextmanager
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connections

import importlib


class QueriesDisabledError(Exception):
    pass


def _raise_exception(execute, sql, params, many, context):
    raise QueriesDisabledError(sql)


def _get_custom_wrapper():
    custom_wrapper_path = getattr(settings, "ZEN_QUERIES_DISABLED_HANDLER", None)
    if custom_wrapper_path:
        module_path, function_name = custom_wrapper_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, function_name, None)


def _disable_queries():
    custom_wrapper = _get_custom_wrapper()

    for connection in connections.all():
        connection.execute_wrappers.append(custom_wrapper or _raise_exception)


def _enable_queries():
    for connection in connections.all():
        connection.execute_wrappers.pop()


def _are_queries_disabled():
    for connection in connections.all():
        return _raise_exception in connection.execute_wrappers


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
