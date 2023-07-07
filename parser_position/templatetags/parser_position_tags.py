from django import template

from core.templatetags import core_tags


register = template.Library()

register.inclusion_tag(
    # todo: настроить так, чтобы линтер находил шаблоны
    "admin/parser_position/preparedposition/change_list_results.html",
    takes_context = True
)(core_tags.results_list_with_context)
