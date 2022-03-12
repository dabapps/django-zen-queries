from django.template import Library, Node

import zen_queries

register = Library()


class QueriesDisabledNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        with zen_queries.queries_disabled():
            return self.nodelist.render(context)


class QueriesDangerouslyEnabledNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        with zen_queries.queries_dangerously_enabled():
            return self.nodelist.render(context)


@register.tag
def queries_disabled(parser, token):
    nodelist = parser.parse(("end_queries_disabled",))
    parser.delete_first_token()
    return QueriesDisabledNode(nodelist)


@register.tag
def queries_dangerously_enabled(parser, token):
    nodelist = parser.parse(("end_queries_dangerously_enabled",))
    parser.delete_first_token()
    return QueriesDangerouslyEnabledNode(nodelist)
