from django.shortcuts import render as django_render
from django.test import TestCase
from rest_framework import serializers
from zen_queries import (
    fetch,
    queries_dangerously_enabled,
    queries_disabled,
    QueriesDisabledError,
    render,
    SimpleTemplateResponse,
    TemplateResponse,
)
from zen_queries.rest_framework import (
    disable_serializer_queries,
    QueriesDisabledSerializerMixin,
    QueriesDisabledViewMixin,
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

    def test_outer_queries_enabled(self):
        # enabling queries should always enable them, and subsequent
        # calls to disable should do nothing
        with queries_dangerously_enabled():
            with queries_disabled():
                Widget.objects.count()

    def test_nested_queries_enabled(self):
        with queries_disabled():
            with queries_disabled():
                with queries_dangerously_enabled():
                    with queries_disabled():
                        with queries_dangerously_enabled():
                            with queries_disabled():
                                Widget.objects.count()
                with self.assertRaises(QueriesDisabledError):
                    Widget.objects.count()
            with self.assertRaises(QueriesDisabledError):
                Widget.objects.count()
        Widget.objects.count()

    def test_sql_in_exception(self):
        queryset = Widget.objects.all()
        with queries_disabled():
            try:
                fetch(queryset)
            except QueriesDisabledError as e:
                self.assertEqual(str(e), str(queryset.query))


class FetchTestCase(TestCase):
    def test_fetch_all(self):
        with queries_disabled():
            widgets = Widget.objects.all()
            with self.assertRaises(QueriesDisabledError):
                fetch(widgets)

    def test_returns_queryset(self):
        widgets = Widget.objects.all()
        fetched_widgets = fetch(widgets)
        self.assertIs(widgets, fetched_widgets)
        self.assertIsNotNone(widgets._result_cache)
        self.assertIsNotNone(fetched_widgets._result_cache)


class RenderShortcutTestCase(TestCase):
    def test_render(self):
        widgets = Widget.objects.all()
        with self.assertRaises(QueriesDisabledError):
            render(None, "template.html", {"widgets": widgets})


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


class TemplateTagTestCase(TestCase):
    def test_queries_disabled_template_tag(self):
        widgets = Widget.objects.all()
        with self.assertRaises(QueriesDisabledError):
            django_render(None, "queries_disabled_tag.html", {"widgets": widgets})

    def test_queries_dangerously_enabled_template_tag(self):
        widgets = Widget.objects.all()
        render(None, "queries_dangerously_enabled_tag.html", {"widgets": widgets})


class WidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Widget
        fields = ["name"]


class QueriesDisabledSerializer(QueriesDisabledSerializerMixin, WidgetSerializer):
    pass


class SerializerMixinTestCase(TestCase):
    def test_serializer_mixin(self):
        serializer = QueriesDisabledSerializer(Widget.objects.all(), many=True)
        with self.assertRaises(QueriesDisabledError):
            serializer.data

    def test_add_mixin_to_instance(self):
        widgets = Widget.objects.all()
        serializer = WidgetSerializer(widgets, many=True)
        serializer = disable_serializer_queries(serializer)
        with self.assertRaises(QueriesDisabledError):
            serializer.data


class FakeRequest(object):
    def __init__(self, method):
        self.method = method


class FakeView(object):
    def get_serializer(self, *args, **kwargs):
        return WidgetSerializer(Widget.objects.all(), many=True)

    def handle_request(self, method):
        self.request = FakeRequest(method)
        return self.get_serializer().data


class QueriesDisabledView(QueriesDisabledViewMixin, FakeView):
    pass


class FakeListView(FakeView):
    def get_serializer(self, *args, **kwargs):
        return WidgetSerializer(list(Widget.objects.all()), many=True)


class QueriesDisabledListView(QueriesDisabledViewMixin, FakeListView):
    pass


class RESTFrameworkViewMixinTestCase(TestCase):
    def test_view_mixin(self):
        view = QueriesDisabledView()
        view.handle_request(method="GET")
        self.assertTrue(
            isinstance(view.get_serializer(), QueriesDisabledSerializerMixin)
        )

    def test_post_ignored(self):
        view = QueriesDisabledView()
        view.handle_request(method="POST")
        self.assertFalse(
            isinstance(view.get_serializer(), QueriesDisabledSerializerMixin)
        )

    def test_serializer_with_list(self):
        view = QueriesDisabledListView()
        view.handle_request(method="GET")
        self.assertTrue(
            isinstance(view.get_serializer(), QueriesDisabledSerializerMixin)
        )
