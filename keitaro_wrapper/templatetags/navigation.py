from django import template
from django.urls import reverse


register = template.Library()


@register.simple_tag
def nav_items():
    """
    Returns list of navigation items for header.
    """
    return [
        {"title": "Создать компанию", "url": reverse("keitaro_wrapper:create_company")},
        {"title": "Редактировать компанию", "url": reverse("keitaro_wrapper:edit_company")},
    ]


