from django.template.response import (
    SimpleTemplateResponse as DjangoSimpleTemplateResponse,
    TemplateResponse as DjangoTemplateResponse,
)
from zen_queries import queries_disabled


class RenderMixin:
    def render(self) -> DjangoSimpleTemplateResponse:
        with queries_disabled():
            return super().render()  # type: ignore


class TemplateResponse(RenderMixin, DjangoTemplateResponse):
    pass


class SimpleTemplateResponse(RenderMixin, DjangoSimpleTemplateResponse):
    pass
