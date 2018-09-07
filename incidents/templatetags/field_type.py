from django import template
register = template.Library()

@register.filter
def field_type(field):
    return field.field.widget.__class__.__name__

@register.filter
def is_checkbox(field):
    return field.field.widget.__class__.__name__.lower() == "checkboxinput"
