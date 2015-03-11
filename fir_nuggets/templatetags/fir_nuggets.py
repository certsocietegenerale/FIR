from django.template import Library

register = Library()

@register.filter
def order_by(queryset, args):
    args = [x.strip() for x in args.split(',')]
    return queryset.order_by(*args)

@register.filter
def has(queryset, args):
	d = {args+"__isnull": False}
	return queryset.filter(**d)

@register.filter
def has_not(queryset, args):
	d = {args+"__isnull": True}
	return queryset.filter(**d)