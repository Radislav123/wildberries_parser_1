from django import template
from django.contrib.admin.templatetags import admin_list


register = template.Library()


# noinspection PyUnresolvedReferences
@register.inclusion_tag("admin/parser/showposition/change_list_results.html", takes_context = True)
def position_results_list(context, cl):
    result = admin_list.result_list(cl)
    result["context"] = context
    return result
