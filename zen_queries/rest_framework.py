from zen_queries import queries_disabled


class QueriesDisabledSerializerMixin:
    @property
    def data(self):
        with queries_disabled():
            return super().data
