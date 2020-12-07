from zen_queries import queries_disabled


class QueriesDisabledSerializerMixin:
    @classmethod
    def many_init(self, *args, **kwargs):
        """
        Ensure queries are also disabled when `many=True`.
        """
        return disable_serializer_queries(super().many_init(*args, **kwargs))

    @property
    def data(self):
        with queries_disabled():
            return super(QueriesDisabledSerializerMixin, self).data


def disable_serializer_queries(serializer):
    serializer.__class__ = type(
        serializer.__class__.__name__,
        (QueriesDisabledSerializerMixin, serializer.__class__),
        {},
    )
    return serializer


class QueriesDisabledViewMixin(object):
    def get_serializer(self, *args, **kwargs):
        serializer = super(QueriesDisabledViewMixin, self).get_serializer(
            *args, **kwargs
        )
        if self.request.method == "GET":
            serializer = disable_serializer_queries(serializer)
            if getattr(serializer, "many", False):
                # Serializer data must be fully evaluated prior to serialization. See #18.
                serializer.instance._fetch_all()
        return serializer
