from django.template.response import TemplateResponse as DjangoTemplateResponse
from django.template.response import (
    SimpleTemplateResponse as DjangoSimpleTemplateResponse,
)
from zen_queries import queries_disabled


class RenderMixin:
    def render(self, *args, **kwargs):
        with queries_disabled():
            return super().render(*args, **kwargs)


class TemplateResponse(RenderMixin, DjangoTemplateResponse):
    pass


class SimpleTemplateResponse(RenderMixin, DjangoSimpleTemplateResponse):
    pass
