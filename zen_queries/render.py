from django.http import HttpRequest, HttpResponse
from django.shortcuts import render as django_render
from typing import Any, Mapping, Optional, Sequence, Union
from zen_queries import queries_disabled


def render(
    request: HttpRequest,
    template_name: Union[str, Sequence[str]],
    context: Optional[Mapping[str, Any]] = None,
    content_type: Optional[str] = None,
    status: Optional[int] = None,
    using: Optional[str] = None,
) -> HttpResponse:
    """
    Wrapper around Django's `render` shortcut that is
    not allowed to run database queries
    """
    with queries_disabled():
        response = django_render(
            request,
            template_name,
            context=context,
            content_type=content_type,
            status=status,
            using=using,
        )
    return response
