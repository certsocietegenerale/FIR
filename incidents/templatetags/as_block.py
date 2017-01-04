from django import template
register = template.Library()


@register.filter(name='as_block')
def as_block(string):
    return "\t{}".format(string.replace("\n", "\n\t"))
