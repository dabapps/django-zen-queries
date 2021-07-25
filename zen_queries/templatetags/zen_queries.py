from django.template import Library, Node
import zen_queries


register = Library()


class RenderNodelistWithContextManagerNode(Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        with self.context_manager:
            return self.nodelist.render(context)


class QueriesDisabledNode(RenderNodelistWithContextManagerNode):
    context_manager = zen_queries.queries_disabled()


class QueriesDangerouslyEnabledNode(RenderNodelistWithContextManagerNode):
    context_manager = zen_queries.queries_dangerously_enabled()


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
