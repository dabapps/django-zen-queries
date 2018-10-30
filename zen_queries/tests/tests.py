from django.test import TestCase
from zen_queries import (
    fetch,
    queries_disabled,
    queries_dangerously_enabled,
    QueriesDisabledError,
    QueriesDisabledSerializerMixin,
    render,
    SimpleTemplateResponse,
    TemplateResponse,
)
from zen_queries.tests.models import Widget


class ContextManagerTestCase(TestCase):
    def test_queries_disabled(self):
        with queries_disabled():
            with self.assertRaises(QueriesDisabledError):
                Widget.objects.count()

    def test_nested_queries_disabled(self):
        with queries_disabled():
            with self.assertRaises(QueriesDisabledError):
                Widget.objects.count()
            with queries_disabled():
                with self.assertRaises(QueriesDisabledError):
                    Widget.objects.count()
                with queries_disabled():
                    with self.assertRaises(QueriesDisabledError):
                        Widget.objects.count()
        Widget.objects.count()

    def test_queries_enabled(self):
        with queries_disabled():
            with queries_dangerously_enabled():
                Widget.objects.count()

        # queries can't be enabled if they've not been disabled
        with self.assertRaises(AssertionError):
            with queries_dangerously_enabled():
                pass

        # enabling queries should always enable them, no matter how deeply
        # nested we are, and should restore the stack afterwards
        with queries_disabled():
            with queries_dangerously_enabled():
                Widget.objects.count()
            with queries_disabled():
                with queries_dangerously_enabled():
                    Widget.objects.count()
                with queries_disabled():
                    with queries_dangerously_enabled():
                        Widget.objects.count()
                    with self.assertRaises(QueriesDisabledError):
                        Widget.objects.count()
                with queries_dangerously_enabled():
                    Widget.objects.count()
                with self.assertRaises(QueriesDisabledError):
                    Widget.objects.count()
            with queries_dangerously_enabled():
                Widget.objects.count()
            with self.assertRaises(QueriesDisabledError):
                Widget.objects.count()
        Widget.objects.count()


class FetchTestCase(TestCase):
    def test_fetch_all(self):
        with queries_disabled():
            widgets = Widget.objects.all()
            with self.assertRaises(QueriesDisabledError):
                fetch(widgets)


class RenderShortcutTestCase(TestCase):
    def test_render(self):
        widgets = Widget.objects.all()
        with self.assertRaises(QueriesDisabledError):
            response = render(None, "template.html", {"widgets": widgets})


class TemplateResponseTestCase(TestCase):
    def test_simple_template_response(self):
        widgets = Widget.objects.all()
        response = SimpleTemplateResponse("template.html", {"widgets": widgets})
        with self.assertRaises(QueriesDisabledError):
            response.render()

    def test_template_response(self):
        widgets = Widget.objects.all()
        response = TemplateResponse(None, "template.html", {"widgets": widgets})
        with self.assertRaises(QueriesDisabledError):
            response.render()


class FakeSerializer(object):
    def __init__(self, queryset):
        self.queryset = queryset

    @property
    def data(self):
        return [item.name for item in self.queryset]


class QueriesDisabledSerializer(QueriesDisabledSerializerMixin, FakeSerializer):
    pass


class SerializerMixinTestCase(TestCase):
    def test_serializer_mixin(self):
        widgets = Widget.objects.all()
        serializer = QueriesDisabledSerializer(widgets)
        with self.assertRaises(QueriesDisabledError):
            serializer.data
