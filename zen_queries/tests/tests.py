from django.test import TestCase
from zen_queries import (
    fetch,
    queries_disabled,
    queries_dangerously_enabled,
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

    def test_add_mixin_to_instance(self):
        widgets = Widget.objects.all()
        serializer = FakeSerializer(widgets)
        serializer = disable_serializer_queries(serializer)
        with self.assertRaises(QueriesDisabledError):
            serializer.data


class FakeRequest(object):
    def __init__(self, method):
        self.method = method


class FakeView(object):
    def get_serializer(self, *args, **kwargs):
        return FakeSerializer(Widget.objects.all())

    def handle_request(self, method):
        self.request = FakeRequest(method)
        return self.get_serializer().data


class QueriesDisabledView(QueriesDisabledViewMixin, FakeView):
    pass


class RESTFrameworkViewMixinTestCase(TestCase):
    def test_view_mixin(self):
        with self.assertRaises(QueriesDisabledError):
            QueriesDisabledView().handle_request(method="GET")

    def test_post_ignored(self):
        QueriesDisabledView().handle_request(method="POST")
