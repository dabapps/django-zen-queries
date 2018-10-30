from django.shortcuts import render as django_render
from zen_queries import queries_disabled


def render(
    request, template_name, context=None, content_type=None, status=None, using=None
):
    with queries_disabled():
        response = django_render(
            request, template_name, context, content_type, status, using
        )
    return response
