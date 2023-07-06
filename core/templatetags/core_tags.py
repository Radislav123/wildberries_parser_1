from django import template
from django.contrib.admin.templatetags import admin_list


register = template.Library()


def results_list_with_context(context, cl):
    result = admin_list.result_list(cl)
    result["context"] = context
    return result
