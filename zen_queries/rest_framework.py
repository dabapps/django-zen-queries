from zen_queries import queries_disabled


class QueriesDisabledSerializerMixin(object):
    @property
    def data(self):
        with queries_disabled():
            return super(QueriesDisabledSerializerMixin, self).data


class QueriesDisabledViewMixin(object):
    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        serializer.__class__ = type(
            serializer.__class__.__name__,
            (QueriesDisabledSerializerMixin, serializer.__class__),
            {},
        )
        return serializer
