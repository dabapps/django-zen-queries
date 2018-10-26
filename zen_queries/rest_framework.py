from zen_queries import queries_disabled


class QueriesDisabledSerializerMixin(object):
    @property
    def data(self):
        with queries_disabled():
            return super(QueriesDisabledSerializerMixin, self).data
