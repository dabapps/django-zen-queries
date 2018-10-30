from django.shortcuts import render as django_render
from zen_queries import queries_disabled


def render(*args, **kwargs):
    """
    Wrapper around Django's `render` shortcut that is
    not allowed to run database queries
    """
    with queries_disabled():
        response = django_render(*args, **kwargs)
    return response
