from zen_queries import queries_disabled


class QueriesDisabledSerializerMixin(object):
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
        return serializer
